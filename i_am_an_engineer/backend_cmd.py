"""Show which backends are registered and configured.

  iae backend status
"""
from __future__ import annotations

from i_am_an_engineer.backends import registry
from i_am_an_engineer.common import emit
from i_am_an_engineer.keys import SERVICES, key_status


def _ensure_backends_loaded() -> None:
    # Import side effects register factories.
    import i_am_an_engineer.backends.elevenlabs  # noqa: F401
    import i_am_an_engineer.backends.fal  # noqa: F401
    import i_am_an_engineer.backends.heygen  # noqa: F401
    import i_am_an_engineer.backends.local  # noqa: F401


def cmd_status(args) -> None:
    _ensure_backends_loaded()
    backends = []
    for name in registry.names():
        try:
            b = registry.create(name)
            st = b.status() if hasattr(b, "status") else {"name": name}
        except Exception as e:  # noqa: BLE001
            st = {"name": name, "error": str(e)}
        backends.append(st)
    keys = {n: {"present": key_status(n)["present"]} for n in SERVICES}
    emit({"backends": backends, "keys": keys}, as_json=True)


def register(sub) -> None:
    import argparse

    p = sub.add_parser(
        "backend",
        help="list configured backends",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sp = p.add_subparsers(dest="cmd", metavar="<command>")
    s = sp.add_parser("status", help="show backend + key status")
    s.set_defaults(func=cmd_status)
