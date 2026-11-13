"""Run pipeline stages — including a no-API dry-run from one iPhone take.

  iae run --plan-only
  iae run ./IMG_1234.MOV --dry-run
  iae run https://example.com/take.mov --dry-run --project /tmp/ad
  iae run --stages ingest,transcribe,compose,export,publish_check
"""
from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from i_am_an_engineer.common import die, emit, ensure_dir, project_dir, which
from i_am_an_engineer.project import init_project, load_project, plan_pipeline, project_yaml_path


def _ensure_project(root: Path, name: str | None = None) -> dict:
    if not project_yaml_path(root).exists():
        init_project(root, name=name or "dry-run-ad")
    return load_project(root)


def dry_run(root: Path, input_ref: str, *, ratios: list[str] | None = None) -> dict:
    """No-API end-to-end: ingest+normalize → transcribe → compose (cut/loudness/captions/framings).

    Uses the founder's normalized recording as the compose plate (stand-in for twin A-roll)
    so the path can be tested without HeyGen/ElevenLabs/fal keys.
    """
    if not which("ffmpeg"):
        die("ffmpeg required for dry-run")
    data = _ensure_project(root)
    if ratios:
        from i_am_an_engineer.project import save_project

        data.setdefault("reframe", {})["ratios"] = ratios
        save_project(root, data)

    # 1) ingest + normalize
    from i_am_an_engineer.ingest import cmd_ingest

    cmd_ingest(
        SimpleNamespace(
            project=str(root),
            files=[input_ref],
            kind="motion",
            force=True,
            no_normalize=False,
            fps=30,
        )
    )

    # Pick normalized master
    motion_dir = root / ((data.get("recordings") or {}).get("motion") or "recordings/motion")
    masters = sorted(motion_dir.glob("*.mp4"))
    if not masters:
        die("dry-run: ingest produced no normalized mp4")
    master = masters[-1]

    # 2) transcribe (stub — no paid ASR)
    from i_am_an_engineer.transcribe import cmd_transcribe

    cmd_transcribe(SimpleNamespace(project=str(root), files=[str(master)], engine="stub"))

    # 3) compose: framings + captions + loudness (−14 LUFS)
    from i_am_an_engineer.compose import cmd_compose

    cmd_compose(
        SimpleNamespace(
            project=str(root),
            aroll=str(master),
            broll=[],
            plan_only=False,
        )
    )

    # 4) export presets (files into exports/)
    from i_am_an_engineer.export import cmd_export

    cmd_export(SimpleNamespace(project=str(root), from_dir=None, platforms=None))

    compose_dir = root / "work" / "compose"
    outputs = sorted(str(p) for p in compose_dir.glob("ad_*.mp4"))
    result = {
        "mode": "dry-run",
        "input": input_ref,
        "normalized": str(master),
        "compose_outputs": outputs,
        "exports_manifest": str(root / "exports" / "manifest.json"),
        "note": "No API backends called. Normalized plate used as A-roll stand-in.",
    }
    (ensure_dir(root / "work") / "dry_run.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8"
    )
    return result


def cmd_run(args) -> None:
    root = project_dir(getattr(args, "project", None))
    input_ref = getattr(args, "input", None)

    if getattr(args, "dry_run", False):
        if not input_ref:
            die("dry-run requires an input path or http(s) URL: iae run <input> --dry-run")
        result = dry_run(
            root,
            input_ref,
            ratios=getattr(args, "ratios", None),
        )
        emit(result, as_json=True)
        return

    data = load_project(root)
    stages = plan_pipeline(data)
    if args.stages:
        wanted = {s.strip() for s in args.stages.split(",") if s.strip()}
        stages = [s for s in stages if s["id"] in wanted]
        for s in stages:
            s["enabled"] = True
    enabled = [s for s in stages if s.get("enabled")]
    if args.plan_only:
        emit({"stages": enabled}, as_json=True)
        return

    if input_ref and not args.allow_api:
        # Convenience: input without --dry-run still ingests first
        from i_am_an_engineer.ingest import cmd_ingest

        cmd_ingest(
            SimpleNamespace(
                project=str(root),
                files=[input_ref],
                kind="motion",
                force=False,
                no_normalize=False,
                fps=30,
            )
        )

    safe = {"ingest", "transcribe", "compose", "export", "publish_check"}
    ran = []
    for stage in enabled:
        sid = stage["id"]
        if sid not in safe and not args.allow_api:
            print(f"skip {sid} (pass --allow-api to run paid backends, or use --dry-run)")
            continue
        if sid == "publish_check":
            from i_am_an_engineer.publish import check

            code = check(root, None)
            if code:
                die("publish check failed; stopping")
            ran.append(sid)
            continue
        if sid == "transcribe":
            from i_am_an_engineer.transcribe import cmd_transcribe

            cmd_transcribe(SimpleNamespace(project=str(root), files=[], engine="stub"))
            ran.append(sid)
            continue
        print(
            f"stage {sid}: not auto-run without --dry-run or explicit inputs; "
            f"see `iae {sid.split('_')[0]} --help`"
        )
    emit({"ran": ran}, as_json=True)


def register(sub) -> None:
    import argparse

    p = sub.add_parser(
        "run",
        help="run pipeline stages (use --dry-run for no-API ingest→compose)",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument(
        "input",
        nargs="?",
        help="local path or http(s) URL to a raw recording (required with --dry-run)",
    )
    p.add_argument("--project")
    p.add_argument("--plan-only", action="store_true")
    p.add_argument("--stages", help="comma-separated stage ids")
    p.add_argument("--allow-api", action="store_true", help="allow paid API stages")
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="no-API path: ingest+normalize, transcribe, compose (captions/loudness/framings), export",
    )
    p.add_argument(
        "--ratios",
        nargs="+",
        default=None,
        help="override reframe ratios for dry-run (default from project.yaml)",
    )
    p.set_defaults(func=cmd_run)
