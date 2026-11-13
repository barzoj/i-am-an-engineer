"""Print the one-session recording guide (English only).

  iae record guide
"""
from __future__ import annotations

from i_am_an_engineer.common import repo_root

GUIDE = """# One recording session (30–60 minutes) — English only

One room, phone or better camera on a stable support, lav if you have one,
window or lamp in front of the face, plain wall, clothes you want the ad to
live in. Lock exposure. You do not need to perform the final ad script.

| Block | Time | What to record |
| --- | --- | --- |
| Setup + consent | 5 min | Each tool's consent take, face-on, clearly. |
| Motion, close / mid | 8–10 min | 2–3 continuous takes, 20–40 s, expressive English talk. Hands visible, eye contact, energy slightly overdone. Then one calmer 20 s take. |
| Two-minute speech | 8–10 min | One uninterrupted ~2 min English monologue; lips close on pauses; 2–3 s silence at start/end. |
| Framing stills | 8–10 min | Hold still 5–10 s each, lips slightly open: close-up, waist-up, three-quarter, full body. Prefer 16:9 and 9:16. |
| Voice, seated | 15–25 min | Calm even English prose into the lav. Target 15–20 min now (30+ for PVC). |
| Optional walk / sit | 5 min | Slow walk into mid-shot, sit, turn to camera. |

After the session: `iae ingest`, train the twin, then lock the English script
and generate. The twin says the script — this session is source material only.

More detail: knowledge/recording/one-session.md
"""


def cmd_guide(args) -> None:
    path = repo_root() / "knowledge" / "recording" / "one-session.md"
    if path.is_file() and not getattr(args, "builtin", False):
        print(path.read_text(encoding="utf-8"))
        return
    print(GUIDE)


def register(sub) -> None:
    import argparse

    p = sub.add_parser(
        "record",
        help="recording-session shot list",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sp = p.add_subparsers(dest="cmd", metavar="<command>")
    g = sp.add_parser("guide", help="print the 30–60 min English shot list")
    g.add_argument("--builtin", action="store_true", help="ignore knowledge/ and print built-in guide")
    g.set_defaults(func=cmd_guide)
