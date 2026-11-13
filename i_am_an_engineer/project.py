"""project.yaml load / validate / scaffold."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml

from i_am_an_engineer.common import die, ensure_dir

SCHEMA_VERSION = 1
ALLOWED_RATIOS = ("9:16", "4:5", "1:1", "16:9")
ALLOWED_PLATFORMS = ("meta", "linkedin")
ALLOWED_TWIN = ("heygen", "local")
ALLOWED_VOICE = ("elevenlabs", "heygen", "auto")
ALLOWED_BROLL = ("fal", "deepinfra", "heygen")
ALLOWED_COMPOSE = ("local", "heygen-studio", "heygen-hyperframes")
ALLOWED_AROLL = ("avatar_v", "avatar_iv", "cinematic_avatar")

DEFAULT_PROJECT: dict[str, Any] = {
    "schema_version": SCHEMA_VERSION,
    "name": "example-ad",
    "language": "en",
    "speaker": {
        "name": "Founder",
        "display_credit": "Founder",
    },
    "script": {
        "path": "script/en.md",
        "target_seconds": [20, 45],
    },
    "recordings": {
        "motion": "recordings/motion/",
        "stills": "recordings/stills/",
        "voice": "recordings/voice/",
    },
    "backends": {
        "twin": "heygen",
        "voice": "auto",
        "broll": "fal",
        "compose": "local",
        "aroll_engine": "avatar_v",
    },
    "heygen": {
        "avatar_group_id": None,
        "look_ids": [],
        "voice_id": None,
    },
    "consent": {
        "path": "consent/likeness.md",
        "granted": False,
    },
    "voice": {
        "elevenlabs_voice_id": None,
        "mode": "tts",
    },
    "broll": {
        "shots": [
            {
                "prompt": "Clean modern desk with soft window light, no people, cinematic",
                "duration_s": 5,
                "model": "fal-ai/veo3.1",
            }
        ]
    },
    "grade": {"lufs": -14},
    "captions": {
        "language": "en",
        "burn_in": True,
        "source": "script",
    },
    "reframe": {
        "ratios": ["9:16", "4:5", "1:1", "16:9"],
        "height": 1080,
    },
    "export": {
        "platforms": ["meta", "linkedin"],
    },
    "disclosure": {
        "enabled": False,
        "label": "Digital twin of {speaker}, from their own recording",
        "burn_in": True,
        "from_first_frame": True,
        "forbid_phrases": [],
    },
}

PROJECT_DIRS = (
    "recordings/motion",
    "recordings/stills",
    "recordings/voice",
    "consent",
    "script",
    "work/ingest",
    "work/transcripts",
    "work/aroll",
    "work/broll",
    "work/audio",
    "work/compose",
    "exports",
)

DEFAULT_SCRIPT = """# English ad script (approved)

Hook: Most founders cannot deliver a calm, confident take on camera.

Body: Record once. Train your digital twin on your own face and voice.
Then generate professional English A-roll, cut with B-roll and captions,
and export for Meta and LinkedIn.

Offer: Start with one 30–60 minute session. The twin says the script.
"""

DEFAULT_CONSENT = """# Likeness and voice consent

I consent to creating a digital twin of my likeness and voice from my own
recordings for producing English advertising videos of myself.

Granted: no  # set to yes / update project.yaml consent.granted after signing
"""


class ProjectError(ValueError):
    pass


def project_yaml_path(root: Path) -> Path:
    return root / "project.yaml"


def load_project(root: Path) -> dict[str, Any]:
    path = project_yaml_path(root)
    if not path.is_file():
        die(f"no project.yaml in {root}; run `iae init` first")
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        die("project.yaml must be a mapping")
    validate_project(raw)
    return raw


def save_project(root: Path, data: dict[str, Any]) -> Path:
    validate_project(data)
    path = project_yaml_path(root)
    path.write_text(
        yaml.safe_dump(data, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    return path


def validate_project(data: dict[str, Any]) -> None:
    errors: list[str] = []
    if data.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION}")
    lang = data.get("language")
    if lang != "en":
        errors.append(f"language must be 'en' (got {lang!r}); English only")
    backends = data.get("backends") or {}
    if backends.get("twin") not in ALLOWED_TWIN:
        errors.append(f"backends.twin must be one of {ALLOWED_TWIN}")
    if backends.get("voice") not in ALLOWED_VOICE:
        errors.append(f"backends.voice must be one of {ALLOWED_VOICE}")
    if backends.get("broll") not in ALLOWED_BROLL:
        errors.append(f"backends.broll must be one of {ALLOWED_BROLL}")
    if backends.get("compose") not in ALLOWED_COMPOSE:
        errors.append(f"backends.compose must be one of {ALLOWED_COMPOSE}")
    if backends.get("aroll_engine") not in ALLOWED_AROLL:
        errors.append(f"backends.aroll_engine must be one of {ALLOWED_AROLL}")
    reframe = data.get("reframe") or {}
    for ratio in reframe.get("ratios") or []:
        if ratio not in ALLOWED_RATIOS:
            errors.append(f"unsupported reframe ratio {ratio!r}")
    export = data.get("export") or {}
    for plat in export.get("platforms") or []:
        if plat not in ALLOWED_PLATFORMS:
            errors.append(f"unsupported export platform {plat!r}")
    disclosure = data.get("disclosure") or {}
    if disclosure.get("enabled") and not disclosure.get("burn_in", True):
        # allowed but publish check will look for consistency elsewhere
        pass
    captions = data.get("captions") or {}
    if captions.get("language") not in (None, "en"):
        errors.append("captions.language must be 'en'")
    if "script" not in data or not isinstance(data.get("script"), dict):
        errors.append("script mapping required")
    if errors:
        raise ProjectError("; ".join(errors))


def plan_pipeline(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Return ordered pipeline stages for `iae run` / tests."""
    stages = [
        {"id": "ingest", "enabled": True},
        {"id": "transcribe", "enabled": True},
        {"id": "twin_create", "enabled": data.get("backends", {}).get("twin") == "heygen"},
        {"id": "twin_consent", "enabled": True},
        {"id": "voice", "enabled": True},
        {"id": "generate_aroll", "enabled": True},
        {"id": "broll", "enabled": True},
        {"id": "compose", "enabled": data.get("backends", {}).get("compose") == "local"},
        {"id": "export", "enabled": True},
        {"id": "publish_check", "enabled": True},
    ]
    return stages


def init_project(root: Path, name: str | None = None, force: bool = False) -> Path:
    root = ensure_dir(root)
    path = project_yaml_path(root)
    if path.exists() and not force:
        die(f"project.yaml already exists at {path} (pass --force to overwrite)")
    data = deepcopy(DEFAULT_PROJECT)
    if name:
        data["name"] = name
        data["speaker"]["name"] = name
        data["speaker"]["display_credit"] = name
    for d in PROJECT_DIRS:
        ensure_dir(root / d)
    script_path = root / data["script"]["path"]
    if not script_path.exists():
        script_path.parent.mkdir(parents=True, exist_ok=True)
        script_path.write_text(DEFAULT_SCRIPT, encoding="utf-8")
    consent_path = root / data["consent"]["path"]
    if not consent_path.exists():
        consent_path.write_text(DEFAULT_CONSENT, encoding="utf-8")
    gitkeep = root / "recordings" / ".gitkeep"
    if not gitkeep.exists():
        gitkeep.write_text("", encoding="utf-8")
    save_project(root, data)
    return path


def script_text(root: Path, data: dict[str, Any] | None = None) -> str:
    data = data or load_project(root)
    rel = (data.get("script") or {}).get("path") or "script/en.md"
    path = root / rel
    if not path.is_file():
        die(f"script not found: {path}")
    return path.read_text(encoding="utf-8")


def teleprompter_lines(script: str) -> list[str]:
    """Flatten markdown script into teleprompter lines (plain English sentences)."""
    lines: list[str] = []
    for raw in script.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.lower().startswith(("hook:", "body:", "offer:")):
            line = line.split(":", 1)[1].strip()
        if line:
            lines.append(line)
    return lines
