"""End-to-end dry-run on a synthetic clip (skip if no ffmpeg)."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from i_am_an_engineer.media import make_synthetic_clip
from i_am_an_engineer.run import dry_run

pytestmark = pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg required")


def test_dry_run_synthetic(tmp_path: Path):
    clip = tmp_path / "sample.mp4"
    make_synthetic_clip(clip, seconds=1.0, width=320, height=240)
    project = tmp_path / "proj"
    result = dry_run(project, str(clip), ratios=["9:16", "1:1"])
    assert result["mode"] == "dry-run"
    assert Path(result["normalized"]).exists()
    assert (project / "work" / "compose" / "ad_9x16.mp4").exists()
    assert (project / "work" / "compose" / "ad_1x1.mp4").exists()
    assert (project / "exports" / "manifest.json").exists()
    meta = json.loads((project / "work" / "dry_run.json").read_text(encoding="utf-8"))
    assert meta["compose_outputs"]
