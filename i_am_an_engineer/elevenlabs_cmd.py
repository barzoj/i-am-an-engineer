"""ElevenLabs backend helpers and key storage.

  iae elevenlabs key set
  iae elevenlabs key status
"""
from __future__ import annotations

from i_am_an_engineer.keys import add_key_subparser


def register(sub) -> None:
    import argparse

    p = sub.add_parser(
        "elevenlabs",
        help="ElevenLabs API key and helpers",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sp = p.add_subparsers(dest="cmd", metavar="<command>")
    add_key_subparser(sp, "elevenlabs")
