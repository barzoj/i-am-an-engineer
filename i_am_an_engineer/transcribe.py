"""Transcribe ingested takes (English). Offline stub + optional whisper CLI.

  iae transcribe
  iae transcribe work/ingest/... --engine stub
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
        "text": f"[stub transcript for {path.name} — replace with whisper or API]",
        "segments": [],
    }


def whisper_transcript(path: Path) -> dict:
    # Prefer `whisper` CLI when present; otherwise fall back to stub without failing CI.
    if not which("whisper"):
        return stub_transcript(path)
    from i_am_an_engineer.common import run

    out_dir = path.parent
    run(["whisper", str(path), "--language", "en", "--output_format", "json", "--output_dir", str(out_dir)])
    js = out_dir / f"{path.stem}.json"
    if js.is_file():
        data = json.loads(js.read_text(encoding="utf-8"))
        return {
            "engine": "whisper",
            "language": "en",
            "text": data.get("text", ""),
            "segments": data.get("segments", []),
        }
    return stub_transcript(path)


def cmd_transcribe(args) -> None:
    root = project_dir(getattr(args, "project", None))
    load_project(root)
    out_dir = ensure_dir(root / "work" / "transcripts")
    engine = getattr(args, "engine", "auto")
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
        if engine == "stub" or (engine == "auto" and not which("whisper")):
            tr = stub_transcript(src)
        else:
            tr = whisper_transcript(src)
        tr.update(
            {
                "source": str(src),
                "transcribed_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        out = out_dir / f"{src.stem}.json"
        out.write_text(json.dumps(tr, indent=2), encoding="utf-8")
        results.append({"source": str(src), "out": str(out), "engine": tr["engine"]})
    emit({"transcripts": results}, as_json=True)


def register(sub) -> None:
    import argparse

    p = sub.add_parser(
        "transcribe",
        help="transcribe ingested takes (English)",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("files", nargs="*", help="optional specific files")
    p.add_argument("--project", help="project directory (default: cwd)")
    p.add_argument("--engine", choices=["auto", "stub", "whisper"], default="auto")
    p.set_defaults(func=cmd_transcribe)
