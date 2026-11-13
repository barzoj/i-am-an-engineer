"""HeyGen backend helpers and key storage.

  iae heygen key set
  iae heygen key status
  iae heygen key verify   # GET /v3/users/me (free)
  iae heygen key clear
"""
from __future__ import annotations

from i_am_an_engineer.keys import add_key_subparser


def register(sub) -> None:
    import argparse

    p = sub.add_parser(
        "heygen",
        help="HeyGen API key and helpers",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sp = p.add_subparsers(dest="cmd", metavar="<command>")
    add_key_subparser(sp, "heygen")
