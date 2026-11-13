"""Local ffmpeg compose: framings, captions, loudness, optional disclosure.

  iae compose --aroll work/aroll/master.mp4 --broll work/broll/*.mp4
  iae compose --plan-only
"""
from __future__ import annotations

import json
import shlex
import subprocess
from pathlib import Path

from i_am_an_engineer.common import die, emit, ensure_dir, project_dir, which
from i_am_an_engineer.project import load_project, script_text, teleprompter_lines

RATIO_TO_SIZE = {
    "9:16": (1080, 1920),
    "4:5": (1080, 1350),
    "1:1": (1080, 1080),
    "16:9": (1920, 1080),
}


def caption_ass(lines: list[str], *, disclosure: str | None = None) -> str:
    """Minimal ASS with English burn-in captions."""
    header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,48,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,2,0,2,40,40,80,1
Style: Disclosure,Arial,28,&H00EEEEEE,&H000000FF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,1,0,7,40,40,40,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    events = []
    if disclosure:
        events.append(
            f"Dialogue: 0,0:00:00.00,0:59:59.00,Disclosure,,0,0,0,,{disclosure.replace(',', '\\,')}"
        )
    t = 0.0
    for line in lines:
        start = _ts(t)
        end = _ts(t + 3.0)
        events.append(
            f"Dialogue: 0,{start},{end},Default,,0,0,0,,{line.replace(',', '\\,')}"
        )
        t += 3.0
    return header + "\n".join(events) + "\n"


def _ts(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h:d}:{m:02d}:{s:05.2f}"


def plan_compose(data: dict, *, aroll: Path | None, broll: list[Path]) -> dict:
    ratios = list((data.get("reframe") or {}).get("ratios") or ["9:16"])
    height = int((data.get("reframe") or {}).get("height") or 1080)
    lufs = float((data.get("grade") or {}).get("lufs") or -14)
    disclosure = data.get("disclosure") or {}
    label = None
    if disclosure.get("enabled") and disclosure.get("burn_in", True):
        speaker = (data.get("speaker") or {}).get("display_credit") or (data.get("speaker") or {}).get("name") or "speaker"
        label = str(disclosure.get("label") or "").replace("{speaker}", speaker)
    return {
        "aroll": str(aroll) if aroll else None,
        "broll": [str(p) for p in broll],
        "ratios": ratios,
        "sizes": {r: RATIO_TO_SIZE.get(r, (1080, height)) for r in ratios},
        "lufs": lufs,
        "captions_burn_in": bool((data.get("captions") or {}).get("burn_in", True)),
        "disclosure_label": label,
        "platforms": list((data.get("export") or {}).get("platforms") or []),
    }


def run_ffmpeg_compose(
    *,
    aroll: Path,
    out: Path,
    size: tuple[int, int],
    ass: Path | None,
    lufs: float,
) -> None:
    w, h = size
    vf = [f"scale={w}:{h}:force_original_aspect_ratio=increase", f"crop={w}:{h}"]
    if ass:
        # Escape for ffmpeg filtergraph
        ass_path = ass.as_posix().replace(":", "\\:").replace("'", "\\'")
        vf.append(f"ass={ass_path}")
    filter_v = ",".join(vf)
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(aroll),
        "-vf",
        filter_v,
        "-af",
        f"loudnorm=I={lufs}:TP=-1.5:LRA=11",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-movflags",
        "+faststart",
        str(out),
    ]
    subprocess.run(cmd, check=True, capture_output=True, text=True)


def cmd_compose(args) -> None:
    root = project_dir(getattr(args, "project", None))
    data = load_project(root)
    aroll = Path(args.aroll) if args.aroll else None
    if aroll and not aroll.is_file():
        aroll = root / args.aroll
    broll: list[Path] = []
    for pattern in args.broll or []:
        p = Path(pattern)
        if p.is_file():
            broll.append(p)
        else:
            broll.extend(sorted(Path().glob(pattern)) or sorted(root.glob(pattern)))
    plan = plan_compose(data, aroll=aroll, broll=broll)
    plan_path = ensure_dir(root / "work" / "compose") / "plan.json"
    plan_path.write_text(json.dumps(plan, indent=2), encoding="utf-8")
    if args.plan_only:
        emit(plan, as_json=True)
        return
    if not aroll or not aroll.is_file():
        die("compose needs --aroll path to an A-roll mp4 (or --plan-only)")
    if not which("ffmpeg"):
        die("ffmpeg not found on PATH")
    lines = teleprompter_lines(script_text(root, data))
    ass_text = caption_ass(lines, disclosure=plan.get("disclosure_label"))
    ass_path = root / "work" / "compose" / "captions.ass"
    ass_path.write_text(ass_text, encoding="utf-8")
    outs = []
    for ratio, size in plan["sizes"].items():
        safe = ratio.replace(":", "x")
        out = root / "work" / "compose" / f"ad_{safe}.mp4"
        run_ffmpeg_compose(
            aroll=aroll,
            out=out,
            size=tuple(size),
            ass=ass_path if plan["captions_burn_in"] else None,
            lufs=float(plan["lufs"]),
        )
        outs.append(str(out))
    emit({"outputs": outs, "plan": str(plan_path)}, as_json=True)


def register(sub) -> None:
    import argparse

    p = sub.add_parser(
        "compose",
        help="cut A-roll + B-roll, captions, loudness, framings",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--aroll", help="A-roll video path")
    p.add_argument("--broll", nargs="*", default=[], help="B-roll clips (reserved for future cut list)")
    p.add_argument("--plan-only", action="store_true", help="write plan.json without running ffmpeg")
    p.add_argument("--project")
    p.set_defaults(func=cmd_compose)
