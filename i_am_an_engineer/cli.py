"""`iae` command line: one entry point for every tool."""
from __future__ import annotations

import argparse
import importlib
import sys

from i_am_an_engineer import __doc_short__ as DOC
from i_am_an_engineer import __version__

GROUPS = [
    "init",
    "doctor",
    "record",
    "script",
    "ingest",
    "transcribe",
    "twin",
    "voice",
    "generate",
    "broll",
    "compose",
    "export",
    "run",
    "publish",
    "kb",
    "backend",
    "heygen",
    "elevenlabs",
    "fal",
    "deepinfra",
]

# Module name overrides when the group name is not the module name.
MODULE_MAP = {
    "init": "init_cmd",
    "script": "script_cmd",
    "backend": "backend_cmd",
    "heygen": "heygen_cmd",
    "elevenlabs": "elevenlabs_cmd",
    "fal": "fal_cmd",
    "deepinfra": "deepinfra_cmd",
}


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError, OSError):
            pass
    ap = argparse.ArgumentParser(
        prog="iae",
        description=DOC,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  iae init --name \"Founder Ad\"\n"
            "  iae record guide\n"
            "  iae script teleprompter --out work/teleprompter.txt\n"
            "  iae heygen key set\n"
            "  iae twin create --footage recordings/motion/take.mp4\n"
            "  iae compose --plan-only\n"
            "  iae publish check\n"
        ),
    )
    ap.add_argument("--version", action="version", version=f"i-am-an-engineer {__version__}")
    sub = ap.add_subparsers(dest="group", metavar="<group>")
    for g in GROUPS:
        mod_name = MODULE_MAP.get(g, g)
        importlib.import_module(f"i_am_an_engineer.{mod_name}").register(sub)
    args = ap.parse_args(argv)
    if not getattr(args, "func", None):
        if args.group:
            ap.parse_args([args.group, "--help"])
        ap.print_help()
        sys.exit(1)
    args.func(args)


if __name__ == "__main__":
    main()
