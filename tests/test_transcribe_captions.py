"""Caption line extraction from transcript JSON."""
from __future__ import annotations

from i_am_an_engineer.compose import caption_ass
from i_am_an_engineer.transcribe import caption_lines_from_transcript


def test_caption_lines_from_segments():
    tr = {
        "engine": "faster-whisper",
        "text": "Hello world. Next line.",
        "segments": [
            {"start": 0.0, "end": 1.2, "text": "Hello world."},
            {"start": 1.2, "end": 2.5, "text": "Next line."},
        ],
    }
    lines = caption_lines_from_transcript(tr)
    assert len(lines) == 2
    assert lines[0]["text"] == "Hello world."
    ass = caption_ass(lines)
    assert "Hello world." in ass
    assert "0:00:00.00" in ass


def test_stub_text_yields_no_lines():
    assert caption_lines_from_transcript({"text": "[stub transcript for x]", "segments": []}) == []
