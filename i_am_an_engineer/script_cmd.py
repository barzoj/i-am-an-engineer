"""Export teleprompter lines from the approved English script.

  iae script teleprompter
  iae script teleprompter --out work/teleprompter.txt
"""
from __future__ import annotations

from pathlib import Path

from i_am_an_engineer.common import die, emit, project_dir
from i_am_an_engineer.project import load_project, script_text, teleprompter_lines


def cmd_teleprompter(args) -> None:
    root = project_dir(getattr(args, "project", None))
    data = load_project(root)
    text = script_text(root, data)
    lines = teleprompter_lines(text)
    if not lines:
        die("no teleprompter lines found in script")
    body = "\n\n".join(lines) + "\n"
    out = getattr(args, "out", None)
    if out:
        path = Path(out)
        if not path.is_absolute():
            path = root / path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
        emit(f"wrote {len(lines)} lines to {path}")
    else:
        print(body, end="")


def register(sub) -> None:
    import argparse

    p = sub.add_parser(
        "script",
        help="script helpers (teleprompter export)",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sp = p.add_subparsers(dest="cmd", metavar="<command>")
    t = sp.add_parser("teleprompter", help="export plain teleprompter lines from script/en.md")
    t.add_argument("--project", help="project directory (default: cwd)")
    t.add_argument("--out", help="output path (default: stdout)")
    t.set_defaults(func=cmd_teleprompter)
