"""Export platform presets (Meta, LinkedIn) + manifest.

  iae export
  iae export --from work/compose
"""
from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from i_am_an_engineer.common import die, emit, ensure_dir, project_dir
from i_am_an_engineer.project import load_project

# Platform preferred ratios (MVP presets).
PLATFORM_RATIOS = {
    "meta": ["9:16", "4:5", "1:1"],
    "linkedin": ["1:1", "9:16", "16:9"],
}


def cmd_export(args) -> None:
    root = project_dir(getattr(args, "project", None))
    data = load_project(root)
    src = Path(args.from_dir) if args.from_dir else root / "work" / "compose"
    if not src.is_absolute():
        src = root / src
    platforms = args.platforms or (data.get("export") or {}).get("platforms") or ["meta", "linkedin"]
    exports_root = ensure_dir(root / "exports")
    items = []
    configured = list((data.get("reframe") or {}).get("ratios") or [])
    for platform in platforms:
        preferred = PLATFORM_RATIOS.get(platform, configured)
        # Only require ratios the project actually composed.
        want = [r for r in preferred if r in configured] if configured else preferred
        plat_dir = ensure_dir(exports_root / platform)
        for ratio in want:
            safe = ratio.replace(":", "x")
            candidate = src / f"ad_{safe}.mp4"
            if not candidate.is_file():
                # still record missing so publish check can fail
                items.append(
                    {
                        "platform": platform,
                        "ratio": ratio,
                        "path": None,
                        "missing": True,
                    }
                )
                continue
            dest = plat_dir / f"{data.get('name', 'ad')}_{safe}.mp4"
            shutil.copy2(candidate, dest)
            items.append(
                {
                    "platform": platform,
                    "ratio": ratio,
                    "path": str(dest.relative_to(root)),
                    "missing": False,
                }
            )
    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "project": data.get("name"),
        "language": data.get("language"),
        "disclosure": data.get("disclosure"),
        "items": items,
    }
    man_path = exports_root / "manifest.json"
    man_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    emit({"manifest": str(man_path), "items": items}, as_json=True)


def register(sub) -> None:
    import argparse

    p = sub.add_parser(
        "export",
        help="write Meta/LinkedIn presets + manifest.json",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--from", dest="from_dir", default=None, help="compose output folder")
    p.add_argument("--platforms", nargs="+", choices=["meta", "linkedin"])
    p.add_argument("--project")
    p.set_defaults(func=cmd_export)
