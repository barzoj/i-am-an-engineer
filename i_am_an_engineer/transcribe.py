"""Transcribe ingested takes (English) with local faster-whisper by default.

  iae transcribe
  iae transcribe recordings/motion/sample.mp4 --engine faster-whisper
  iae transcribe --engine stub   # tests only
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from i_am_an_engineer.common import die, emit, ensure_dir, project_dir, which
from i_am_an_engineer.project import load_project

AUDIO_VIDEO = {".mp4", ".mov", ".webm", ".mkv", ".wav", ".m4a", ".mp3", ".aac"}


def stub_transcript(path: Path) -> dict:
    return {
        "engine": "stub",
        "language": "en",
        "text": f"[stub transcript for {path.name} — replace with faster-whisper]",
        "segments": [],
    }


def _extract_wav_for_asr(path: Path, wav: Path) -> Path:
    """Decode to 16 kHz mono PCM with ffmpeg (avoids PyAV version skew with faster-whisper)."""
    from i_am_an_engineer.common import run

    if not which("ffmpeg"):
        die("ffmpeg required to extract audio for faster-whisper")
    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(path),
            "-vn",
            "-acodec",
            "pcm_s16le",
            "-ar",
            "16000",
            "-ac",
            "1",
            str(wav),
        ],
        check=True,
    )
    return wav


def faster_whisper_transcript(
    path: Path,
    *,
    model_size: str = "tiny",
) -> dict:
    """Local ASR via faster-whisper (English). Downloads the model on first use."""
    import tempfile

    try:
        from faster_whisper import WhisperModel
    except ImportError as e:
        die(
            "faster-whisper is not installed. From the repo: ensure `bin/iae` ran via uv, "
            "or `uv sync`. Original error: " + str(e)
        )
    import wave

    import numpy as np

    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    with tempfile.TemporaryDirectory() as td:
        wav = Path(td) / "asr.wav"
        _extract_wav_for_asr(path, wav)
        # Load PCM ourselves so we never hit PyAV's av.open(..., metadata_errors=...)
        # which breaks on some av 19.x builds bundled with faster-whisper.
        with wave.open(str(wav), "rb") as wf:
            if wf.getnchannels() != 1 or wf.getsampwidth() != 2:
                die("ASR wav must be 16-bit mono (ffmpeg extract failed)")
            rate = wf.getframerate()
            raw = wf.readframes(wf.getnframes())
        audio = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
        if rate != 16000:
            # rare — ffmpeg asked for 16k; resample roughly if not
            duration = len(audio) / float(rate)
            target = int(duration * 16000)
            audio = np.interp(
                np.linspace(0, len(audio), target, endpoint=False),
                np.arange(len(audio)),
                audio,
            ).astype(np.float32)
        segments_iter, info = model.transcribe(audio, language="en", vad_filter=True)
        segments = []
        parts = []
        for seg in segments_iter:
            text = (seg.text or "").strip()
            if not text:
                continue
            segments.append(
                {
                    "start": float(seg.start),
                    "end": float(seg.end),
                    "text": text,
                }
            )
            parts.append(text)
    return {
        "engine": "faster-whisper",
        "model": model_size,
        "language": getattr(info, "language", "en") or "en",
        "text": " ".join(parts).strip(),
        "segments": segments,
    }


def whisper_cli_transcript(path: Path) -> dict:
    if not which("whisper"):
        return stub_transcript(path)
    from i_am_an_engineer.common import run

    out_dir = path.parent
    run(
        [
            "whisper",
            str(path),
            "--language",
            "en",
            "--output_format",
            "json",
            "--output_dir",
            str(out_dir),
        ]
    )
    js = out_dir / f"{path.stem}.json"
    if js.is_file():
        data = json.loads(js.read_text(encoding="utf-8"))
        return {
            "engine": "whisper-cli",
            "language": "en",
            "text": data.get("text", ""),
            "segments": data.get("segments", []),
        }
    return stub_transcript(path)


def run_transcribe(path: Path, engine: str = "auto", *, model_size: str = "tiny") -> dict:
    if engine == "stub":
        return stub_transcript(path)
    if engine == "whisper":
        return whisper_cli_transcript(path)
    if engine in ("faster-whisper", "auto"):
        try:
            return faster_whisper_transcript(path, model_size=model_size)
        except SystemExit:
            raise
        except Exception as e:  # noqa: BLE001
            if engine == "faster-whisper":
                die(f"faster-whisper failed: {e}")
            # auto: try CLI whisper, else stub (unit tests without model download)
            if which("whisper"):
                return whisper_cli_transcript(path)
            raise
    die(f"unknown engine {engine!r}")


def caption_lines_from_transcript(tr: dict) -> list[dict]:
    """Return [{start, end, text}, ...] for ASS burn-in."""
    segs = tr.get("segments") or []
    out = []
    for seg in segs:
        text = str(seg.get("text") or "").strip()
        if not text:
            continue
        out.append(
            {
                "start": float(seg.get("start") or 0),
                "end": float(seg.get("end") or (float(seg.get("start") or 0) + 2)),
                "text": text,
            }
        )
    if out:
        return out
    text = str(tr.get("text") or "").strip()
    if not text or text.startswith("[stub"):
        return []
    # Fall back: split on sentence boundaries, 3s each
    import re

    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
    t = 0.0
    for s in sentences:
        out.append({"start": t, "end": t + 3.0, "text": s})
        t += 3.0
    return out


def cmd_transcribe(args) -> None:
    root = project_dir(getattr(args, "project", None))
    load_project(root)
    out_dir = ensure_dir(root / "work" / "transcripts")
    engine = getattr(args, "engine", "auto")
    model_size = getattr(args, "model", "tiny")
    inputs: list[Path] = []
    if args.files:
        inputs = [Path(f) for f in args.files]
    else:
        for sub in ("motion", "voice"):
            d = root / "recordings" / sub
            if d.is_dir():
                inputs.extend(p for p in d.iterdir() if p.suffix.lower() in AUDIO_VIDEO)
    if not inputs:
        die("no audio/video takes found; run `iae ingest` first or pass files")
    results = []
    for src in inputs:
        src = src if src.is_absolute() else (root / src if (root / src).exists() else Path(src))
        if not src.is_file():
            die(f"missing file: {src}")
        tr = run_transcribe(src, engine=engine, model_size=model_size)
        tr.update(
            {
                "source": str(src),
                "transcribed_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        out = out_dir / f"{src.stem}.json"
        out.write_text(json.dumps(tr, indent=2), encoding="utf-8")
        results.append(
            {
                "source": str(src),
                "out": str(out),
                "engine": tr["engine"],
                "chars": len(tr.get("text") or ""),
            }
        )
    emit({"transcripts": results}, as_json=True)


def register(sub) -> None:
    import argparse

    p = sub.add_parser(
        "transcribe",
        help="transcribe ingested takes with local faster-whisper (English)",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("files", nargs="*", help="optional specific files")
    p.add_argument("--project", help="project directory (default: cwd)")
    p.add_argument(
        "--engine",
        choices=["auto", "faster-whisper", "whisper", "stub"],
        default="auto",
        help="auto prefers faster-whisper (required for dry-run captions)",
    )
    p.add_argument("--model", default="tiny", help="faster-whisper model size (default: tiny)")
    p.set_defaults(func=cmd_transcribe)
