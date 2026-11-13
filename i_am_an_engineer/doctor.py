"""Check the local toolchain and configured backends.

  iae doctor
  iae doctor --json
  iae doctor --keys          # summary + free verify for each present key
  iae doctor --keys --json
"""
from __future__ import annotations

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


def _print_keys_summary(info: dict, verify_rows: list[dict] | None = None) -> None:
    print("--- keys ---")
    by_name = {r["service"]: r for r in (verify_rows or [])}
    for name, st in info["keys"].items():
        line = f"key {name}: "
        if st["present"]:
            line += f"{st['masked']} via {st['source']}"
        else:
            line += "not set"
        vr = by_name.get(name)
        if vr is not None:
            if vr.get("ok") is True:
                line += "  [verify OK]"
            elif vr.get("ok") is False:
                line += f"  [verify FAIL: {vr.get('error') or vr.get('message')}]"
            elif not st["present"]:
                line += "  [verify skipped]"
        print(line)
        if vr and vr.get("ok") and vr.get("summary"):
            bits = []
            for k in (
                "billing_type",
                "subscription_tier",
                "credits_balance",
                "currency",
                "character_limit",
            ):
                if vr["summary"].get(k) is not None:
                    bits.append(f"{k}={vr['summary'][k]}")
            if bits:
                print(f"       {' '.join(bits)}")


def cmd_doctor(args) -> None:
    root = project_dir(getattr(args, "project", None))
    info = collect(root if (root / "project.yaml").exists() else None)
    verify_payload = None
    if getattr(args, "keys", False):
        from i_am_an_engineer.verify import verify_all

        verify_payload = verify_all(only_present=True)
        info["key_verify"] = verify_payload

    if getattr(args, "json", False):
        emit(info, as_json=True)
    else:
        print(f"i-am-an-engineer {info['version']}  python {info['python']}")
        print(f"ffmpeg:  {info['ffmpeg'] or 'MISSING (required for compose)'}")
        print(f"ffprobe: {info['ffprobe'] or 'missing (optional)'}")
        if getattr(args, "keys", False):
            _print_keys_summary(info, (verify_payload or {}).get("keys"))
            print("verify uses free account endpoints only (no twin/TTS/B-roll spend)")
        else:
            for name, st in info["keys"].items():
                if st["present"]:
                    print(f"key {name}: {st['masked']} via {st['source']}")
                else:
                    print(f"key {name}: not set")
            print("(pass --keys to verify each present key with a free authenticated call)")
        if info["project"]:
            if info["project"]["ok"]:
                print(f"project: {info['project']['name']} ({info['project']['path']})")
            else:
                print(f"project: INVALID — {info['project']['error']}")

    exit_bad = not info["ok"]
    if verify_payload is not None:
        # Fail doctor --keys only when a *present* key fails verify
        for row in verify_payload.get("keys") or []:
            if row.get("present") and row.get("ok") is False:
                exit_bad = True
    if exit_bad:
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
    p.add_argument(
        "--keys",
        action="store_true",
        help="print key summary and verify each present key (free account endpoints)",
    )
    p.set_defaults(func=cmd_doctor)
