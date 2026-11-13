"""Show which backends are registered and configured.

  iae backend status

Always exits 0 and lists every backend + key — missing keys are reported, not fatal.
"""
from __future__ import annotations

from i_am_an_engineer.backends import registry
from i_am_an_engineer.common import emit
from i_am_an_engineer.keys import SERVICES, key_status

BACKEND_ROLES = {
    "heygen": "twin+aroll",
    "elevenlabs": "voice",
    "fal": "broll",
    "local": "twin stub",
    "local-gpu": "twin stub",
}


def _ensure_backends_loaded() -> None:
    import i_am_an_engineer.backends.elevenlabs  # noqa: F401
    import i_am_an_engineer.backends.fal  # noqa: F401
    import i_am_an_engineer.backends.heygen  # noqa: F401
    import i_am_an_engineer.backends.local  # noqa: F401


def cmd_status(args) -> None:
    """Unified status board; never raises / never exits non-zero for missing keys."""
    _ensure_backends_loaded()
    keys = {}
    for name in SERVICES:
        try:
            st = key_status(name)
            keys[name] = {
                "present": bool(st.get("present")),
                "source": st.get("source"),
                "masked": st.get("key"),
            }
        except Exception as e:  # noqa: BLE001
            keys[name] = {"present": False, "error": str(e)}

    backends = []
    for name in registry.names():
        row: dict = {
            "name": name,
            "role": BACKEND_ROLES.get(name, "unknown"),
            "configured": False,
        }
        try:
            b = registry.create(name)
            st = b.status() if hasattr(b, "status") else {"name": name}
            if isinstance(st, dict):
                row.update(st)
            row["configured"] = bool(row.get("configured") or row.get("key_present"))
        except SystemExit as e:
            # resolve_key dies with SystemExit — treat as not configured
            row["configured"] = False
            row["error"] = f"exit {getattr(e, 'code', 1)}"
        except Exception as e:  # noqa: BLE001
            row["configured"] = False
            row["error"] = str(e)
        backends.append(row)

    payload = {
        "backends": backends,
        "keys": keys,
        "ok": True,
        "note": "Missing keys are expected before setup-backends; this command always succeeds.",
    }
    if getattr(args, "json", True) or True:
        emit(payload, as_json=True)


def register(sub) -> None:
    import argparse

    p = sub.add_parser(
        "backend",
        help="list configured backends (never fails on missing keys)",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sp = p.add_subparsers(dest="cmd", metavar="<command>")
    s = sp.add_parser("status", help="show every backend + key; exit 0 even when keys missing")
    s.set_defaults(func=cmd_status)
