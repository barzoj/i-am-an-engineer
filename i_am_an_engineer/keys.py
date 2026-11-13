"""API key storage: env wins, then OS keyring (Linux secret-tool), else ~/.secrets.

  iae heygen key set
  iae elevenlabs key set
  iae fal key set
  iae deepinfra key set
"""
from __future__ import annotations

import getpass
import os
import re
import shutil
import stat
import subprocess
from dataclasses import dataclass
from pathlib import Path

from i_am_an_engineer.common import die, text_utf8

KEYRING_TIMEOUT = 20
_DEFAULT_SECRETS = "~/.secrets"


@dataclass(frozen=True)
class Service:
    name: str
    env_var: str
    keyring_service: str
    keyring_key: str = "api"
    file_name: str | None = None
    docs_url: str = ""

    @property
    def label(self) -> str:
        return f"{self.keyring_service} API key (i-am-an-engineer)"

    @property
    def key_file_name(self) -> str:
        return self.file_name or f"{self.name}-key"


SERVICES: dict[str, Service] = {
    "heygen": Service(
        name="heygen",
        env_var="HEYGEN_API_KEY",
        keyring_service="heygen.com",
        docs_url="https://platform.heygen.com",
    ),
    "elevenlabs": Service(
        name="elevenlabs",
        env_var="ELEVENLABS_API_KEY",
        keyring_service="elevenlabs.io",
        docs_url="https://elevenlabs.io/app/settings/api-keys",
    ),
    "fal": Service(
        name="fal",
        env_var="FAL_KEY",
        keyring_service="fal.ai",
        docs_url="https://fal.ai/dashboard/keys",
    ),
    "deepinfra": Service(
        name="deepinfra",
        env_var="DEEPINFRA_API_KEY",
        keyring_service="deepinfra.com",
        docs_url="https://deepinfra.com/dash/api_keys",
    ),
}


def get_service(name: str) -> Service:
    if name not in SERVICES:
        die(f"unknown service {name!r}; choose one of: {', '.join(SERVICES)}")
    return SERVICES[name]


def key_file(svc: Service) -> Path:
    override = os.environ.get(f"IAE_{svc.name.upper()}_KEY_FILE") or os.environ.get(
        f"{svc.env_var}_FILE"
    )
    if override:
        return Path(override).expanduser()
    return Path(_DEFAULT_SECRETS).expanduser() / svc.key_file_name


def mask(k: str) -> str:
    return (k[:6] + "…" + k[-4:]) if len(k) > 14 else "…"


def _secret_tool(*args: str, value: str | None = None) -> subprocess.CompletedProcess | None:
    st = shutil.which("secret-tool")
    if not st:
        return None
    try:
        return subprocess.run(
            [st, *args],
            input=value,
            capture_output=True,
            timeout=KEYRING_TIMEOUT,
            **text_utf8(),
        )
    except (OSError, subprocess.SubprocessError):
        return None


def keyring_available() -> bool:
    return shutil.which("secret-tool") is not None


def keyring_attrs(svc: Service) -> list[str]:
    return ["service", svc.keyring_service, "key", svc.keyring_key]


def keyring_get(svc: Service) -> str | None:
    r = _secret_tool("lookup", *keyring_attrs(svc))
    return (r.stdout.strip() or None) if r and r.returncode == 0 else None


def keyring_set(svc: Service, value: str) -> bool:
    r = _secret_tool("store", "--label", svc.label, *keyring_attrs(svc), value=value)
    return bool(r and r.returncode == 0)


def keyring_clear(svc: Service) -> bool:
    r = _secret_tool("clear", *keyring_attrs(svc))
    return bool(r and r.returncode == 0)


def write_key_file(value: str, path: Path) -> Path:
    p = path.expanduser()
    if not p.parent.exists():
        p.parent.mkdir(mode=0o700, parents=True)
    fd = os.open(p, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        if hasattr(os, "fchmod"):
            os.fchmod(f.fileno(), 0o600)
        f.write(value.strip() + "\n")
    return p


def file_mode(p: Path) -> str:
    try:
        return oct(stat.S_IMODE(p.stat().st_mode))
    except OSError:
        return "?"


def _read_file(p: Path) -> str | None:
    try:
        return p.read_text().strip() or None
    except OSError:
        return None


def _read_dotenv(path: Path, env_var: str) -> str | None:
    try:
        m = re.search(
            rf"^\s*{re.escape(env_var)}\s*=\s*['\"]?([^'\"\s]+)",
            path.read_text(),
            re.M,
        )
    except OSError:
        return None
    return m.group(1) if m else None


def _dotenv_files() -> list[Path]:
    from i_am_an_engineer.common import repo_root

    return list(dict.fromkeys((Path.cwd() / ".env", repo_root() / ".env")))


def key_candidates(svc: Service):
    """(label, reader, plaintext) in precedence order. Env wins."""
    yield (
        f"{svc.env_var} environment variable",
        lambda: (os.environ.get(svc.env_var) or "").strip() or None,
        False,
    )
    named = os.environ.get(f"IAE_{svc.name.upper()}_KEY_FILE") or os.environ.get(
        f"{svc.env_var}_FILE"
    )
    kf = key_file(svc)
    if named:
        yield f"key file {kf}", lambda: _read_file(kf), False
    yield f"OS keyring ({' '.join(keyring_attrs(svc))})", lambda: keyring_get(svc), False
    if not named:
        yield f"plaintext file {kf} (mode {file_mode(kf)})", lambda: _read_file(kf), True
    for env in _dotenv_files():
        yield (
            f".env file {env}",
            lambda env=env: _read_dotenv(env, svc.env_var),
            True,
        )


def resolve_key(svc: Service | str, *, required: bool = True) -> str | None:
    if isinstance(svc, str):
        svc = get_service(svc)
    for _label, read, _plaintext in key_candidates(svc):
        k = read()
        if k:
            return k
    if required:
        hint = f"Create one at {svc.docs_url}, then `iae {svc.name} key set`" if svc.docs_url else f"`iae {svc.name} key set`"
        die(f"no {svc.name} key. {hint} (or set {svc.env_var})")
    return None


def key_status(svc: Service | str) -> dict:
    if isinstance(svc, str):
        svc = get_service(svc)
    for label, read, _ in key_candidates(svc):
        k = read()
        if k:
            return {"service": svc.name, "source": label, "key": mask(k), "present": True}
    return {"service": svc.name, "source": None, "key": None, "present": False}


def cmd_key(
    svc_name: str,
    action: str,
    *,
    from_file: str | None = None,
    as_json: bool = False,
) -> None:
    svc = get_service(svc_name)
    kf = key_file(svc)
    if action == "set":
        if from_file:
            value = Path(from_file).expanduser().read_text().strip()
        else:
            value = getpass.getpass(f"{svc.name} API key (hidden): ").strip()
        if not value:
            die("empty key, nothing stored")
        if keyring_available() and keyring_set(svc, value):
            print(f"stored {svc.name} key in OS keyring ({' '.join(keyring_attrs(svc))})")
            return
        write_key_file(value, kf)
        print(f"stored {svc.name} key in {kf} (mode {file_mode(kf)})")
        return
    if action == "status":
        st = key_status(svc)
        if st["present"]:
            print(f"{svc.name}: {st['key']} via {st['source']}")
        else:
            print(f"{svc.name}: not set (env {svc.env_var} / keyring / {kf})")
        return
    if action == "verify":
        from i_am_an_engineer.common import emit
        from i_am_an_engineer.verify import verify_service

        result = verify_service(svc_name)
        if as_json:
            emit(result, as_json=True)
        else:
            status = "OK" if result.get("ok") else "FAIL"
            print(f"{svc.name} key verify: {status} — {result.get('message') or result.get('error')}")
            if result.get("summary"):
                for k, v in result["summary"].items():
                    if v is not None and k != "http_status":
                        print(f"  {k}: {v}")
            print(f"  endpoint: {result.get('endpoint')} ({result.get('cost')})")
        if not result.get("ok"):
            raise SystemExit(1)
        return
    if action == "clear":
        cleared = []
        if keyring_available() and keyring_clear(svc):
            cleared.append("keyring")
        if kf.exists():
            kf.unlink()
            cleared.append(str(kf))
        print(f"cleared {svc.name}: {', '.join(cleared) or 'nothing stored'}")
        return
    die(f"unknown key action {action!r}")


def add_key_subparser(parent, service: str) -> None:
    """Attach `key set|status|verify|clear` under a backend group."""
    p = parent.add_parser("key", help=f"store / show / verify / clear the {service} API key")
    sp = p.add_subparsers(dest="key_action", metavar="<action>")
    s = sp.add_parser("set", help="store the key (keyring or ~/.secrets)")
    s.add_argument("--from-file", help="read the key from a file instead of a hidden prompt")
    s.set_defaults(func=lambda a, svc=service: cmd_key(svc, "set", from_file=a.from_file))
    st = sp.add_parser("status", help="show which source provides the key (masked)")
    st.set_defaults(func=lambda a, svc=service: cmd_key(svc, "status"))
    v = sp.add_parser(
        "verify",
        help="cheap authenticated call to validate the key (no generation spend)",
    )
    v.add_argument("--json", action="store_true", help="print JSON result")
    v.set_defaults(func=lambda a, svc=service: cmd_key(svc, "verify", as_json=a.json))
    c = sp.add_parser("clear", help="remove the stored key")
    c.set_defaults(func=lambda a, svc=service: cmd_key(svc, "clear"))
