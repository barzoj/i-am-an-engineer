"""Knowledge base: search, new, check, index.

  iae kb search "heygen api"
  iae kb new --title "Recording session notes" --kind recording
  iae kb check --index
  iae kb index
"""
from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path

from i_am_an_engineer.common import die, emit, repo_root

REQUIRED_SECTIONS = ("Summary", "Gotchas")


def knowledge_root() -> Path:
    return repo_root() / "knowledge"


def iter_notes() -> list[Path]:
    root = knowledge_root()
    if not root.is_dir():
        return []
    return sorted(p for p in root.rglob("*.md") if p.name not in {"INDEX.md", "README.md", "TEMPLATE.md"})


def parse_frontmatter(text: str) -> tuple[dict, str]:
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    meta: dict = {}
    for line in parts[1].strip().splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip().strip("\"'")
    return meta, parts[2]


def cmd_search(args) -> None:
    q = args.query.lower()
    hits = []
    for path in iter_notes():
        text = path.read_text(encoding="utf-8", errors="replace")
        if q in text.lower() or q in path.as_posix().lower():
            meta, _ = parse_frontmatter(text)
            hits.append(
                {
                    "path": str(path.relative_to(repo_root())),
                    "title": meta.get("title") or path.stem,
                }
            )
    emit({"hits": hits}, as_json=True)


def cmd_new(args) -> None:
    kind = args.kind or "backends"
    root = knowledge_root() / kind
    root.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^a-z0-9]+", "-", args.title.lower()).strip("-")[:80]
    path = root / f"{slug}.md"
    if path.exists() and not args.force:
        die(f"exists: {path}")
    body = f"""---
title: {args.title}
date: {date.today().isoformat()}
status: draft
agents: []
---

# {args.title}

## Summary

TODO

## Gotchas

1. TODO
"""
    path.write_text(body, encoding="utf-8")
    emit(f"wrote {path}")


def check_note(path: Path) -> list[str]:
    fails = []
    text = path.read_text(encoding="utf-8", errors="replace")
    meta, body = parse_frontmatter(text)
    if "TODO" in body and meta.get("status") == "published":
        fails.append(f"{path.name}: published note still has TODO")
    for section in REQUIRED_SECTIONS:
        if f"## {section}" not in body:
            fails.append(f"{path.name}: missing ## {section}")
    if re.search(r"(HEYGEN_API_KEY|ELEVENLABS_API_KEY|FAL_KEY)\s*=\s*\S+", text):
        fails.append(f"{path.name}: looks like a secret assignment")
    return fails


def cmd_check(args) -> None:
    fails: list[str] = []
    paths = [Path(p) for p in args.paths] if args.paths else iter_notes()
    for path in paths:
        if not path.is_file():
            path = repo_root() / path
        fails.extend(check_note(path))
    if args.index:
        cmd_index(args)
        idx = knowledge_root() / "INDEX.md"
        if not idx.is_file():
            fails.append("INDEX.md missing after index")
    for f in fails:
        print("FAIL ", f)
    print(("FAIL" if fails else "PASS") + f": {len(fails)} failures")
    raise SystemExit(1 if fails else 0)


def cmd_index(args) -> None:
    notes = []
    for path in iter_notes():
        meta, _ = parse_frontmatter(path.read_text(encoding="utf-8", errors="replace"))
        rel = path.relative_to(knowledge_root()).as_posix()
        notes.append({"path": rel, "title": meta.get("title") or path.stem, "date": meta.get("date")})
    notes.sort(key=lambda n: n.get("date") or "", reverse=True)
    lines = ["# Knowledge index", ""]
    for n in notes:
        lines.append(f"- [{n['title']}]({n['path']})")
    (knowledge_root() / "INDEX.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (knowledge_root() / "index.json").write_text(json.dumps(notes, indent=2), encoding="utf-8")
    emit(f"indexed {len(notes)} notes")


def register(sub) -> None:
    import argparse

    p = sub.add_parser(
        "kb",
        help="knowledge base search / new / check / index",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sp = p.add_subparsers(dest="cmd", metavar="<command>")
    s = sp.add_parser("search", help="search notes")
    s.add_argument("query")
    s.set_defaults(func=cmd_search)
    n = sp.add_parser("new", help="scaffold a note")
    n.add_argument("--title", required=True)
    n.add_argument("--kind", default="backends")
    n.add_argument("--force", action="store_true")
    n.set_defaults(func=cmd_new)
    c = sp.add_parser("check", help="lint notes")
    c.add_argument("paths", nargs="*")
    c.add_argument("--index", action="store_true")
    c.set_defaults(func=cmd_check)
    i = sp.add_parser("index", help="rebuild INDEX.md and index.json")
    i.set_defaults(func=cmd_index)
