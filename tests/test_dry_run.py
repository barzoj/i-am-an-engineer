"""End-to-end dry-run on a spoken sample (skip if no ffmpeg/espeak)."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from i_am_an_engineer.media import make_spoken_sample
from i_am_an_engineer.run import dry_run

pytestmark = [
    pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg required"),
    pytest.mark.skipif(
        shutil.which("espeak-ng") is None and shutil.which("espeak") is None,
        reason="espeak-ng required for spoken dry-run sample",
    ),
]


def test_dry_run_spoken_captions_from_asr(tmp_path: Path):
    clip = tmp_path / "sample.mov"
    make_spoken_sample(clip)
    project = tmp_path / "proj"
    result = dry_run(project, str(clip), ratios=["9:16", "1:1"])
    assert result["mode"] == "dry-run"
    assert result["caption_source"] == "transcript"
    assert result["transcript_engine"] == "faster-whisper"
    tr = json.loads(Path(result["transcript"]).read_text(encoding="utf-8"))
    assert tr["engine"] == "faster-whisper"
    assert tr.get("text") and not str(tr["text"]).startswith("[stub")
    assert (project / "work" / "compose" / "ad_9x16.mp4").exists()
    ass = (project / "work" / "compose" / "captions.ass").read_text(encoding="utf-8")
    assert "Dialogue:" in ass
    plan = json.loads((project / "work" / "compose" / "plan.json").read_text(encoding="utf-8"))
    assert str(plan.get("caption_source", "")).startswith("transcript:")
