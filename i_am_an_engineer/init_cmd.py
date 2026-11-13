"""Scaffold a new digital-twin ad project.

  iae init
  iae init --name "Acme Ad" --project ./ads/acme
  iae init --force
"""
from __future__ import annotations

from i_am_an_engineer.common import emit, project_dir
from i_am_an_engineer.project import init_project


def cmd_init(args) -> None:
    root = project_dir(getattr(args, "project", None))
    path = init_project(root, name=getattr(args, "name", None), force=bool(getattr(args, "force", False)))
    emit(f"initialized project at {path}")


def register(sub) -> None:
    import argparse

    p = sub.add_parser(
        "init",
        help="scaffold project.yaml and folders",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--project", help="project directory (default: cwd)")
    p.add_argument("--name", help="project / speaker display name")
    p.add_argument("--force", action="store_true", help="overwrite existing project.yaml")
    p.set_defaults(func=cmd_init)
