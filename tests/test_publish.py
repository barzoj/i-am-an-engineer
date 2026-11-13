"""publish check consistency."""
from __future__ import annotations

import json
from pathlib import Path

from i_am_an_engineer.project import init_project
from i_am_an_engineer.publish import check_project, check_repo


def test_publish_ok_fresh_project(tmp_path: Path):
    init_project(tmp_path, name="X")
    fails, _warns = check_project(tmp_path)
    assert fails == []


def test_publish_fails_consent_after_generate(tmp_path: Path):
    init_project(tmp_path, name="X")
    aroll = tmp_path / "work" / "aroll"
    aroll.mkdir(parents=True, exist_ok=True)
    (aroll / "vid.json").write_text(json.dumps({"video_id": "1"}), encoding="utf-8")
    fails, _ = check_project(tmp_path)
    assert any("consent" in f for f in fails)


def test_repo_blocks_env(tmp_path: Path):
    (tmp_path / "ok.md").write_text("hi", encoding="utf-8")
    # Build the assignment at runtime so this test file itself does not trip publish check.
    assignment = "HEYGEN_" + "API_KEY=" + ("x" * 24)
    (tmp_path / ".env").write_text(assignment + "\n", encoding="utf-8")
    fails, _ = check_repo(tmp_path)
    assert any("env" in f.lower() or "secret" in f.lower() or "HeyGen" in f for f in fails)
