"""skills/ copies must match .agents/skills and .claude/skills."""
from __future__ import annotations

import filecmp
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _skill_files(base: Path) -> dict[str, Path]:
    return {p.relative_to(base).as_posix(): p for p in base.rglob("SKILL.md")}


def test_skill_copies_match():
    src = _skill_files(ROOT / "skills")
    assert "make-founder-ad/SKILL.md" in src
    for dest_name in (".agents/skills", ".claude/skills"):
        dest_root = ROOT / dest_name
        dest = _skill_files(dest_root)
        assert set(src) == set(dest), f"{dest_name} skill set differs from skills/"
        for rel, sp in src.items():
            dp = dest[rel]
            assert filecmp.cmp(sp, dp, shallow=False), f"{dest_name}/{rel} out of sync"


def test_entry_skill_discovery_hooks():
    text = (ROOT / "skills" / "make-founder-ad" / "SKILL.md").read_text(encoding="utf-8")
    assert "make me an ad" in text
    assert "dry-run" in text
    assert name_frontmatter(text) == "make-founder-ad"


def name_frontmatter(text: str) -> str:
    for line in text.splitlines()[:10]:
        if line.startswith("name:"):
            return line.split(":", 1)[1].strip()
    return ""
