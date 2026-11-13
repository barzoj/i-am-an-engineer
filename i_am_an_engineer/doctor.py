"""Check the local toolchain and configured backends.

  iae doctor
  iae doctor --json
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

from i_am_an_engineer import __version__
from i_am_an_engineer.common import emit, project_dir, which
from i_am_an_engineer.keys import SERVICES, key_status


def collect(project: Path | None = None) -> dict:
    ffmpeg = which("ffmpeg")
    ffprobe = which("ffprobe")
    keys = {name: key_status(name) for name in SERVICES}
    proj = None
    if project and (project / "project.yaml").exists():
        from i_am_an_engineer.project import load_project

        try:
            data = load_project(project)
            proj = {"path": str(project), "name": data.get("name"), "ok": True}
        except Exception as e:  # noqa: BLE001
            proj = {"path": str(project), "ok": False, "error": str(e)}
    return {
        "version": __version__,
        "python": sys.version.split()[0],
        "ffmpeg": ffmpeg,
        "ffprobe": ffprobe,
        "keys": {
            k: {"present": v["present"], "source": v["source"], "masked": v["key"]}
            for k, v in keys.items()
        },
        "project": proj,
        "ok": bool(ffmpeg),
    }


def cmd_doctor(args) -> None:
    root = project_dir(getattr(args, "project", None))
    info = collect(root if (root / "project.yaml").exists() else None)
    if getattr(args, "json", False):
        emit(info, as_json=True)
        return
    print(f"i-am-an-engineer {info['version']}  python {info['python']}")
    print(f"ffmpeg:  {info['ffmpeg'] or 'MISSING (required for compose)'}")
    print(f"ffprobe: {info['ffprobe'] or 'missing (optional)'}")
    for name, st in info["keys"].items():
        if st["present"]:
            print(f"key {name}: {st['masked']} via {st['source']}")
        else:
            print(f"key {name}: not set")
    if info["project"]:
        if info["project"]["ok"]:
            print(f"project: {info['project']['name']} ({info['project']['path']})")
        else:
            print(f"project: INVALID — {info['project']['error']}")
    if not info["ok"]:
        raise SystemExit(1)


def register(sub) -> None:
    import argparse

    p = sub.add_parser(
        "doctor",
        help="check Python, ffmpeg, keys, project",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--project", help="project directory (default: cwd)")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_doctor)
