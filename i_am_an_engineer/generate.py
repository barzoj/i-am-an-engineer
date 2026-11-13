"""Generate A-roll via HeyGen Avatar V/IV or cinematic.

  iae generate aroll --ratios 9:16 4:5
  iae generate cinematic --ratio 9:16
"""
from __future__ import annotations

import json
from pathlib import Path

from i_am_an_engineer.backends.heygen import HeyGenTwinBackend
from i_am_an_engineer.common import die, emit, ensure_dir, project_dir
from i_am_an_engineer.project import load_project, script_text, teleprompter_lines


def _script(root, data, override: str | None) -> str:
    if override:
        return override
    return " ".join(teleprompter_lines(script_text(root, data)))


def cmd_aroll(args) -> None:
    root = project_dir(getattr(args, "project", None))
    data = load_project(root)
    if not (data.get("consent") or {}).get("granted"):
        die("consent.granted is false; complete `iae twin consent` first")
    hey = data.get("heygen") or {}
    look_ids = list(hey.get("look_ids") or [])
    avatar_id = args.avatar_id or (look_ids[0] if look_ids else hey.get("avatar_group_id"))
    if not avatar_id:
        die("no avatar/look id; run `iae twin create` first")
    engine = args.engine or (data.get("backends") or {}).get("aroll_engine") or "avatar_v"
    ratios = args.ratios or (data.get("reframe") or {}).get("ratios") or ["9:16"]
    script = _script(root, data, args.script)
    backend = HeyGenTwinBackend()
    out_dir = ensure_dir(root / "work" / "aroll")
    jobs = []
    for ratio in ratios:
        job = backend.render_aroll(
            avatar_id=str(avatar_id),
            script=script,
            voice_id=hey.get("voice_id"),
            aspect_ratio=ratio,
            engine=engine,
        )
        meta = {
            "video_id": job.video_id,
            "status": job.status,
            "aspect_ratio": ratio,
            "engine": engine,
            "download_url": job.download_url,
        }
        (out_dir / f"{job.video_id}.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
        jobs.append(meta)
    emit({"jobs": jobs}, as_json=True)


def cmd_cinematic(args) -> None:
    args.engine = "cinematic_avatar"
    args.ratios = [args.ratio]
    args.script = getattr(args, "script", None)
    cmd_aroll(args)


def register(sub) -> None:
    import argparse

    p = sub.add_parser(
        "generate",
        help="render A-roll (Avatar V/IV) or cinematic",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sp = p.add_subparsers(dest="cmd", metavar="<command>")
    a = sp.add_parser("aroll", help="Avatar V (default) or IV A-roll for one or more ratios")
    a.add_argument("--ratios", nargs="+", default=None)
    a.add_argument("--engine", choices=["avatar_v", "avatar_iv", "cinematic_avatar"])
    a.add_argument("--avatar-id")
    a.add_argument("--script", help="override script text")
    a.add_argument("--project")
    a.set_defaults(func=cmd_aroll)
    c = sp.add_parser("cinematic", help="cinematic_avatar render")
    c.add_argument("--ratio", default="9:16")
    c.add_argument("--avatar-id")
    c.add_argument("--script")
    c.add_argument("--project")
    c.set_defaults(func=cmd_cinematic)
