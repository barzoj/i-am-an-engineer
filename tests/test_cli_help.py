"""Every CLI group has --help."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GROUPS = [
    "init",
    "doctor",
    "record",
    "script",
    "ingest",
    "transcribe",
    "twin",
    "voice",
    "generate",
    "broll",
    "compose",
    "export",
    "run",
    "publish",
    "kb",
    "backend",
    "heygen",
    "elevenlabs",
    "fal",
    "deepinfra",
]


def _run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "i_am_an_engineer", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        env={**dict(**__import__("os").environ), "PYTHONPATH": str(ROOT)},
    )


def test_root_help():
    r = _run(["--help"])
    assert r.returncode == 0
    assert "iae" in r.stdout.lower() or "digital" in r.stdout.lower()


def test_group_help():
    for g in GROUPS:
        r = _run([g, "--help"])
        assert r.returncode == 0, f"{g} --help failed: {r.stderr}"
