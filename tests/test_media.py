"""Media URL helpers, normalize filter graph, synthetic clip dry pieces."""
from __future__ import annotations

from pathlib import Path

import pytest

from i_am_an_engineer.media import (
    build_normalize_vf,
    guess_filename_from_url,
    is_url,
    looks_hdr,
    make_synthetic_clip,
    resolve_share_url,
)


def test_is_url():
    assert is_url("https://example.com/a.mov")
    assert is_url("http://x.test/y")
    assert not is_url("./IMG_1.MOV")
    assert not is_url("/tmp/a.mov")


def test_resolve_google_drive():
    url = "https://drive.google.com/file/d/abc123XYZ/view?usp=sharing"
    assert "uc?export=download" in resolve_share_url(url)
    assert "abc123XYZ" in resolve_share_url(url)


def test_guess_filename():
    assert guess_filename_from_url("https://x.test/path/IMG_9.MOV") == "IMG_9.MOV"
    assert guess_filename_from_url("https://x.test/d", "video/quicktime") == "recording.mov"


def test_build_normalize_vf_sdr():
    vf = build_normalize_vf(fps=30, hdr=False)
    assert "fps=30" in vf
    assert "yuv420p" in vf


def test_looks_hdr():
    probe = {
        "streams": [
            {
                "codec_type": "video",
                "color_transfer": "smpte2084",
                "color_primaries": "bt2020",
            }
        ]
    }
    assert looks_hdr(probe) is True
    assert looks_hdr({"streams": [{"codec_type": "video", "color_transfer": "bt709"}]}) is False


@pytest.mark.skipif(
    __import__("shutil").which("ffmpeg") is None, reason="ffmpeg not installed"
)
def test_synthetic_clip(tmp_path: Path):
    out = tmp_path / "s.mp4"
    make_synthetic_clip(out, seconds=0.5, width=160, height=120)
    assert out.exists() and out.stat().st_size > 500
