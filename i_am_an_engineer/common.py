"""Shared helpers for the iae CLI."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


def die(msg: str, code: int = 1) -> None:
    print(f"iae: {msg}", file=sys.stderr)
    raise SystemExit(code)


def emit(obj, as_json: bool = False) -> None:
    if as_json or not isinstance(obj, str):
        print(json.dumps(obj, indent=2, default=str))
    else:
        print(obj)


def text_utf8(**kw) -> dict:
    return dict(text=True, encoding="utf-8", errors="replace", **kw)


def run(
    cmd: list[str],
    check: bool = True,
    capture: bool = True,
    timeout: float | None = None,
    **kw,
) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(
            cmd, check=check, capture_output=capture, timeout=timeout, **text_utf8(), **kw
        )
    except FileNotFoundError:
        die(f"not found: {cmd[0]}")
    except subprocess.TimeoutExpired:
        die(f"{' '.join(map(str, cmd[:3]))}... timed out after {timeout}s")
    except subprocess.CalledProcessError as e:
        die(
            f"{' '.join(map(str, cmd[:3]))}... failed ({e.returncode}):\n"
            f"{(e.stderr or e.stdout or '').strip()[-2000:]}"
        )


def which(name: str) -> str | None:
    return shutil.which(name)


def sha256_file(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def repo_root() -> Path:
    """Repository root when running from a clone; else the package parent."""
    here = Path(__file__).resolve().parent
    candidate = here.parent
    if (candidate / "pyproject.toml").exists():
        return candidate
    return here


def project_dir(explicit: str | Path | None = None) -> Path:
    if explicit:
        return Path(explicit).expanduser().resolve()
    env = os.environ.get("IAE_PROJECT")
    if env:
        return Path(env).expanduser().resolve()
    return Path.cwd().resolve()


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path
