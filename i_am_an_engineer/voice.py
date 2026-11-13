"""Voice clone + TTS / STS.

  iae voice clone --samples recordings/voice/*.wav --provider elevenlabs
  iae voice tts --out work/audio/script.mp3
  iae voice sts --audio take.wav --out work/audio/sts.mp3
"""
from __future__ import annotations

from pathlib import Path

from i_am_an_engineer.backends.elevenlabs import ElevenLabsVoiceBackend
from i_am_an_engineer.backends.heygen import HeyGenVoiceBackend
from i_am_an_engineer.common import die, emit, project_dir
from i_am_an_engineer.project import load_project, save_project, script_text, teleprompter_lines


def _samples(root: Path, patterns: list[str]) -> list[Path]:
    files: list[Path] = []
    for pat in patterns:
        p = Path(pat)
        if p.is_file():
            files.append(p)
        else:
            hits = list(Path().glob(pat)) or list(root.glob(pat))
            files.extend(hits)
    return files


def cmd_clone(args) -> None:
    root = project_dir(getattr(args, "project", None))
    data = load_project(root)
    provider = args.provider or (
        "elevenlabs"
        if (data.get("backends") or {}).get("voice") == "elevenlabs"
        else "elevenlabs"
    )
    samples = _samples(root, args.samples)
    if not samples:
        # default to recordings/voice
        voice_dir = root / ((data.get("recordings") or {}).get("voice") or "recordings/voice")
        samples = [p for p in voice_dir.glob("*") if p.is_file()]
    if not samples:
        die("no voice samples found")
    name = args.name or data.get("speaker", {}).get("name") or "founder-voice"
    if provider == "elevenlabs":
        backend = ElevenLabsVoiceBackend()
        result = backend.clone_instant(samples, name=name)
        data.setdefault("voice", {})["elevenlabs_voice_id"] = result.voice_id
        if (data.get("backends") or {}).get("voice") == "auto":
            data["backends"]["voice"] = "elevenlabs"
    elif provider == "heygen":
        backend = HeyGenVoiceBackend()
        result = backend.clone_instant(samples, name=name)
        data.setdefault("heygen", {})["voice_id"] = result.voice_id
    else:
        die(f"unknown provider {provider}")
    save_project(root, data)
    emit({"voice_id": result.voice_id, "provider": result.provider}, as_json=True)


def cmd_tts(args) -> None:
    root = project_dir(getattr(args, "project", None))
    data = load_project(root)
    text = args.text
    if not text:
        lines = teleprompter_lines(script_text(root, data))
        text = " ".join(lines)
    out = Path(args.out)
    if not out.is_absolute():
        out = root / out
    voice_backend = (data.get("backends") or {}).get("voice", "auto")
    if voice_backend in ("elevenlabs", "auto") and (data.get("voice") or {}).get("elevenlabs_voice_id"):
        vid = data["voice"]["elevenlabs_voice_id"]
        ElevenLabsVoiceBackend().tts(text, vid, out)
        provider = "elevenlabs"
    elif (data.get("heygen") or {}).get("voice_id"):
        vid = data["heygen"]["voice_id"]
        HeyGenVoiceBackend().tts(text, vid, out)
        provider = "heygen"
    else:
        die("no voice_id configured; run `iae voice clone` or set heygen.voice_id")
    emit({"out": str(out), "provider": provider, "chars": len(text)}, as_json=True)


def cmd_sts(args) -> None:
    root = project_dir(getattr(args, "project", None))
    data = load_project(root)
    audio = Path(args.audio)
    if not audio.is_file():
        audio = root / args.audio
    out = Path(args.out)
    if not out.is_absolute():
        out = root / out
    if (data.get("voice") or {}).get("elevenlabs_voice_id"):
        vid = data["voice"]["elevenlabs_voice_id"]
        ElevenLabsVoiceBackend().sts(audio, vid, out)
        provider = "elevenlabs"
    elif (data.get("heygen") or {}).get("voice_id"):
        vid = data["heygen"]["voice_id"]
        HeyGenVoiceBackend().sts(audio, vid, out)
        provider = "heygen"
    else:
        die("no voice_id configured")
    emit({"out": str(out), "provider": provider}, as_json=True)


def register(sub) -> None:
    import argparse

    p = sub.add_parser(
        "voice",
        help="clone voice and run TTS/STS",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sp = p.add_subparsers(dest="cmd", metavar="<command>")
    c = sp.add_parser("clone", help="instant voice clone from session audio")
    c.add_argument("--samples", nargs="*", default=[], help="audio files / globs")
    c.add_argument("--provider", choices=["elevenlabs", "heygen"])
    c.add_argument("--name")
    c.add_argument("--project")
    c.set_defaults(func=cmd_clone)
    t = sp.add_parser("tts", help="render approved script with the clone")
    t.add_argument("--text", help="override script text")
    t.add_argument("--out", default="work/audio/script.mp3")
    t.add_argument("--project")
    t.set_defaults(func=cmd_tts)
    s = sp.add_parser("sts", help="speech-to-speech with the clone")
    s.add_argument("--audio", required=True)
    s.add_argument("--out", default="work/audio/sts.mp3")
    s.add_argument("--project")
    s.set_defaults(func=cmd_sts)
