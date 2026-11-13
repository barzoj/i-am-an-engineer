"""Generate B-roll clips (fal Veo 3.1 first).

  iae broll
  iae broll --prompt "soft light over a lab bench" --duration 5
"""
from __future__ import annotations

import json
from pathlib import Path

from i_am_an_engineer.backends.fal import DEFAULT_MODEL, FalBrollBackend
from i_am_an_engineer.common import die, emit, ensure_dir, project_dir
from i_am_an_engineer.project import load_project


def cmd_broll(args) -> None:
    root = project_dir(getattr(args, "project", None))
    data = load_project(root)
    backend_name = (data.get("backends") or {}).get("broll", "fal")
    if backend_name != "fal":
        die(f"broll backend {backend_name!r} not in MVP; use fal")
    shots = []
    if args.prompt:
        shots.append(
            {
                "prompt": args.prompt,
                "duration_s": args.duration,
                "model": args.model or DEFAULT_MODEL,
            }
        )
    else:
        shots = list((data.get("broll") or {}).get("shots") or [])
    if not shots:
        die("no B-roll shots; pass --prompt or set broll.shots in project.yaml")
    out_dir = ensure_dir(root / "work" / "broll")
    backend = FalBrollBackend()
    results = []
    for i, shot in enumerate(shots):
        clip = backend.generate(
            shot["prompt"],
            duration_s=float(shot.get("duration_s", 5)),
            model=shot.get("model") or DEFAULT_MODEL,
            out_dir=out_dir,
        )
        meta = {
            "index": i,
            "prompt": clip.prompt,
            "duration_s": clip.duration_s,
            "model": clip.model,
            "job_id": clip.job_id,
            "path": str(clip.path) if clip.path else None,
            "url": clip.url,
        }
        (out_dir / f"shot_{i}.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
        results.append(meta)
    emit({"clips": results}, as_json=True)


def register(sub) -> None:
    import argparse

    p = sub.add_parser(
        "broll",
        help="generate B-roll via fal Veo 3.1",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--prompt", help="single-shot prompt (otherwise project.yaml broll.shots)")
    p.add_argument("--duration", type=float, default=5.0)
    p.add_argument("--model", default=None)
    p.add_argument("--project")
    p.set_defaults(func=cmd_broll)
