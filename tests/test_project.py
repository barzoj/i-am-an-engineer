"""project.yaml schema and pipeline planning."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest

from i_am_an_engineer.project import (
    DEFAULT_PROJECT,
    ProjectError,
    init_project,
    plan_pipeline,
    teleprompter_lines,
    validate_project,
)


def test_default_project_valid():
    validate_project(deepcopy(DEFAULT_PROJECT))


def test_rejects_non_english():
    data = deepcopy(DEFAULT_PROJECT)
    data["language"] = "de"
    with pytest.raises(ProjectError, match="English"):
        validate_project(data)


def test_rejects_bad_ratio():
    data = deepcopy(DEFAULT_PROJECT)
    data["reframe"]["ratios"] = ["21:9"]
    with pytest.raises(ProjectError, match="ratio"):
        validate_project(data)


def test_plan_pipeline_includes_publish():
    stages = plan_pipeline(deepcopy(DEFAULT_PROJECT))
    ids = [s["id"] for s in stages]
    assert "ingest" in ids
    assert "generate_aroll" in ids
    assert "publish_check" in ids
    assert all("enabled" in s for s in stages)


def test_teleprompter_lines():
    script = "# Title\n\nHook: Pain here.\n\nBody: We help.\n\nOffer: Book a call.\n"
    lines = teleprompter_lines(script)
    assert lines == ["Pain here.", "We help.", "Book a call."]


def test_init_project(tmp_path: Path):
    path = init_project(tmp_path, name="Acme")
    assert path.exists()
    assert (tmp_path / "script" / "en.md").exists()
    assert (tmp_path / "recordings" / "motion").is_dir()
