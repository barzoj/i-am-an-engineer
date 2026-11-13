"""Publish checks: project consistency + block secrets / personal media in git.

  iae publish check
  iae publish check --repo .
"""
from __future__ import annotations

import re
from pathlib import Path

from i_am_an_engineer.common import die, emit, project_dir
from i_am_an_engineer.project import ProjectError, load_project, validate_project

SECRET_PATTERNS = [
    ("HeyGen key assignment", re.compile(r"HEYGEN_API_KEY\s*[=:]\s*['\"]?[A-Za-z0-9_\-]{16,}")),
    ("ElevenLabs key", re.compile(r"ELEVENLABS_API_KEY\s*[=:]\s*['\"]?[A-Za-z0-9_\-]{16,}")),
    ("FAL_KEY assignment", re.compile(r"FAL_KEY\s*[=:]\s*['\"]?[A-Za-z0-9:_\-]{16,}")),
    ("DeepInfra key", re.compile(r"DEEPINFRA_API_KEY\s*[=:]\s*['\"]?[A-Za-z0-9_\-]{16,}")),
    ("Anthropic key", re.compile(r"sk-ant-[A-Za-z0-9_\-]{20,}")),
    ("OpenAI key", re.compile(r"\bsk-(?:(?:proj|svcacct|admin)-[A-Za-z0-9_\-]{32,}|[A-Za-z0-9]{32,})")),
    ("GitHub token", re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{60,})")),
    ("private key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
]

SKIP_DIRS = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    "work",
    "exports",
    "recordings",
}
TEXT_EXT = {
    ".py",
    ".md",
    ".yml",
    ".yaml",
    ".json",
    ".toml",
    ".txt",
    ".sh",
    ".ts",
    ".js",
    ".env",
}
MEDIA_EXT = {".mp4", ".mov", ".webm", ".mkv", ".wav", ".m4a", ".mp3", ".aac"}
BLOCKED_NAMES = {".env", "fal-key", "heygen-key", "elevenlabs-key", "deepinfra-key"}


def check_project(root: Path) -> tuple[list[str], list[str]]:
    fails: list[str] = []
    warns: list[str] = []
    try:
        data = load_project(root)
    except SystemExit as e:
        # load_project dies on missing file
        fails.append(str(e))
        return fails, warns
    except ProjectError as e:
        fails.append(str(e))
        return fails, warns

    try:
        validate_project(data)
    except ProjectError as e:
        fails.append(str(e))

    consent = data.get("consent") or {}
    if not consent.get("granted"):
        # Only fail when generate artifacts exist
        aroll = root / "work" / "aroll"
        if aroll.exists() and any(aroll.glob("*.json")):
            fails.append("generate ran but consent.granted is false")

    disclosure = data.get("disclosure") or {}
    if disclosure.get("enabled") and not disclosure.get("burn_in", True):
        fails.append("disclosure.enabled is true but disclosure.burn_in is false (inconsistent)")
    if not disclosure.get("enabled") and disclosure.get("burn_in") is False:
        # fine
        pass
    # Inconsistent: disabled but compose plan asked for a label burn that was forced
    plan = root / "work" / "compose" / "plan.json"
    if plan.is_file():
        import json

        try:
            p = json.loads(plan.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            p = {}
        if not disclosure.get("enabled") and p.get("disclosure_label"):
            fails.append("disclosure.enabled is false but compose plan has a disclosure_label")
        if disclosure.get("enabled") and disclosure.get("burn_in", True) and not p.get("disclosure_label"):
            fails.append("disclosure.enabled is true but compose plan is missing disclosure_label")

    forbid = list(disclosure.get("forbid_phrases") or [])
    if forbid:
        from i_am_an_engineer.project import script_text

        text = script_text(root, data).lower()
        for phrase in forbid:
            if phrase.lower() in text:
                fails.append(f"forbidden phrase present in script: {phrase!r}")

    # Export completeness
    manifest = root / "exports" / "manifest.json"
    if manifest.is_file():
        import json

        man = json.loads(manifest.read_text(encoding="utf-8"))
        for item in man.get("items") or []:
            if item.get("missing"):
                fails.append(
                    f"missing export for {item.get('platform')} ratio {item.get('ratio')}"
                )

    return fails, warns


def _git_ignored(repo: Path, path: Path) -> bool:
    """True when git check-ignore says the path is ignored (or .git missing → use suffix heuristics)."""
    import subprocess

    git = repo / ".git"
    if not git.exists():
        # Heuristic: common media / scaffolding names are treated as ignored
        name = path.name
        if name in {"ADLOG.md", "ACCEPTANCE_REPORT.md", "project.yaml", "sample.mov"}:
            return True
        if path.suffix.lower() in MEDIA_EXT:
            return True
        return False
    try:
        r = subprocess.run(
            ["git", "-C", str(repo), "check-ignore", "-q", str(path)],
            capture_output=True,
        )
        return r.returncode == 0
    except OSError:
        return False


def check_repo(repo: Path) -> tuple[list[str], list[str]]:
    fails: list[str] = []
    warns: list[str] = []
    files = [
        p
        for p in repo.rglob("*")
        if p.is_file() and not SKIP_DIRS.intersection(p.relative_to(repo).parts)
    ]
    for f in files:
        rel = f.relative_to(repo).as_posix()
        ignored = _git_ignored(repo, f)
        if f.name in BLOCKED_NAMES or f.name.endswith(".env"):
            if not ignored:
                fails.append(f"secret/env file tracked: {rel}")
            continue
        if f.suffix.lower() in MEDIA_EXT and "examples/fixture-readme" not in rel:
            if ignored:
                # Local dry-run artifacts (sample.mov etc.) are gitignored — do not warn.
                continue
            # Block personal media outside licensed fixture
            if any(part in rel for part in ("recordings/", "exports/", "work/", "consent/")):
                fails.append(f"media file that should not be committed: {rel}")
            elif f.stat().st_size > 100_000:
                warns.append(f"large media file in repo: {rel}")
        if f.suffix.lower() in TEXT_EXT or f.name in BLOCKED_NAMES:
            if ignored:
                continue
            try:
                txt = f.read_text(errors="replace")
            except OSError:
                continue
            for label, rx in SECRET_PATTERNS:
                if rx.search(txt):
                    fails.append(f"{label} in {rel}")
    return fails, warns


def check(root: Path | None = None, repo: Path | None = None) -> int:
    fails: list[str] = []
    warns: list[str] = []
    if root and (root / "project.yaml").exists():
        f, w = check_project(root)
        fails.extend(f)
        warns.extend(w)
    if repo:
        f, w = check_repo(repo)
        fails.extend(f)
        warns.extend(w)
    for x in fails:
        print("FAIL ", x)
    for x in warns:
        print("WARN ", x)
    status = "FAIL" if fails else ("WARN" if warns else "PASS")
    print(f"{status}: {len(fails)} failures, {len(warns)} warnings")
    return 1 if fails else 0


def cmd_check(args) -> None:
    root = project_dir(getattr(args, "project", None))
    repo = None
    if getattr(args, "path", None):
        repo = Path(args.path).resolve()
    elif getattr(args, "repo", None):
        repo = Path(args.repo).resolve()
    elif getattr(args, "include_repo", False):
        repo = root
    # Default: if cwd looks like the toolkit repo, also scan it
    if repo is None and (root / "pyproject.toml").exists() and (root / "i_am_an_engineer").is_dir():
        repo = root
    code = check(root if (root / "project.yaml").exists() else None, repo)
    raise SystemExit(code)


def register(sub) -> None:
    import argparse

    p = sub.add_parser(
        "publish",
        help="consistency and safety checks before sharing",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sp = p.add_subparsers(dest="cmd", metavar="<command>")
    c = sp.add_parser("check", help="check project.yaml consistency and blocked media/secrets")
    c.add_argument(
        "path",
        nargs="?",
        help="optional repo/project folder to scan (same as --repo)",
    )
    c.add_argument("--project")
    c.add_argument("--repo", help="also scan this git tree for media/secrets")
    c.add_argument("--include-repo", action="store_true", help="scan --project as a repo tree")
    c.set_defaults(func=cmd_check)
