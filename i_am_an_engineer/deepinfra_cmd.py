"""DeepInfra key storage (optional later B-roll backend).

  iae deepinfra key set
"""
from __future__ import annotations

from i_am_an_engineer.keys import add_key_subparser


def register(sub) -> None:
    import argparse

    p = sub.add_parser(
        "deepinfra",
        help="DeepInfra API key helpers",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sp = p.add_subparsers(dest="cmd", metavar="<command>")
    add_key_subparser(sp, "deepinfra")
