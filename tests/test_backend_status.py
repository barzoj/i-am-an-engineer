"""iae backend status must list all backends and exit 0 without keys."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_backend_status_no_keys():
    env = {**os.environ, "PYTHONPATH": str(ROOT)}
    # Ensure env keys don't leak into the test
    for k in list(env):
        if k.endswith("_API_KEY") or k in {"FAL_KEY", "HEYGEN_API_KEY", "ELEVENLABS_API_KEY"}:
            env.pop(k, None)
    r = subprocess.run(
        [sys.executable, "-m", "i_am_an_engineer", "backend", "status"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        env=env,
    )
    assert r.returncode == 0, r.stderr
    data = json.loads(r.stdout)
    assert data.get("ok") is True
    names = {b["name"] for b in data["backends"]}
    assert "heygen" in names
    assert "elevenlabs" in names
    assert "fal" in names
    assert data["keys"]["heygen"]["present"] is False or isinstance(data["keys"]["heygen"]["present"], bool)
