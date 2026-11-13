"""Digital twin: create, consent wait, extra looks.

  iae twin create --footage recordings/motion/take1.mp4
  iae twin consent
  iae twin looks --prompt "navy blazer, soft studio light"
"""
from __future__ import annotations

from pathlib import Path

from i_am_an_engineer.backends.heygen import HeyGenTwinBackend
from i_am_an_engineer.common import die, emit, project_dir
from i_am_an_engineer.project import load_project, save_project


def _backend(data) -> HeyGenTwinBackend:
    twin = (data.get("backends") or {}).get("twin", "heygen")
    if twin != "heygen":
        die(f"twin backend {twin!r} not implemented for create; use heygen")
    return HeyGenTwinBackend()


def cmd_create(args) -> None:
    root = project_dir(getattr(args, "project", None))
    data = load_project(root)
    footage = Path(args.footage)
    if not footage.is_file():
        footage = root / args.footage
    if not footage.is_file():
        die(f"footage not found: {args.footage}")
    backend = _backend(data)
    name = args.name or data.get("speaker", {}).get("name") or data.get("name") or "founder"
    result = backend.create_digital_twin(footage, name=name)
    data.setdefault("heygen", {})
    data["heygen"]["avatar_group_id"] = result.avatar_group_id
    if result.look_id:
        looks = list(data["heygen"].get("look_ids") or [])
        if result.look_id not in looks:
            looks.append(result.look_id)
        data["heygen"]["look_ids"] = looks
    if result.default_voice_id:
        data["heygen"]["voice_id"] = result.default_voice_id
    save_project(root, data)
    emit(
        {
            "avatar_group_id": result.avatar_group_id,
            "look_id": result.look_id,
            "default_voice_id": result.default_voice_id,
            "status": result.status,
        },
        as_json=True,
    )


def cmd_consent(args) -> None:
    root = project_dir(getattr(args, "project", None))
    data = load_project(root)
    group = args.group_id or (data.get("heygen") or {}).get("avatar_group_id")
    if not group:
        die("no avatar_group_id; run `iae twin create` first or pass --group-id")
    if args.mark_granted:
        data.setdefault("consent", {})["granted"] = True
        save_project(root, data)
        emit("consent.granted set to true in project.yaml")
        return
    backend = _backend(data)
    info = backend.request_consent(str(group))
    url = info.get("consent_url")
    emit(
        {
            "consent_url": url,
            "message": "Open the consent URL in a browser and complete the on-camera statement. "
            "Then `iae twin consent --mark-granted`.",
            "expires_in_hours": info.get("expires_in_hours"),
        },
        as_json=True,
    )


def cmd_looks(args) -> None:
    root = project_dir(getattr(args, "project", None))
    data = load_project(root)
    # Looks generation is API-backed; for MVP we record the prompt intent and note the endpoint.
    emit(
        {
            "status": "planned",
            "prompt": args.prompt,
            "hint": "POST /v3/avatars or /v3/avatars/looks with the prompt; "
            "wire when credits allow. Avatar group: "
            f"{(data.get('heygen') or {}).get('avatar_group_id')}",
        },
        as_json=True,
    )


def register(sub) -> None:
    import argparse

    p = sub.add_parser(
        "twin",
        help="create digital twin, consent, looks",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sp = p.add_subparsers(dest="cmd", metavar="<command>")
    c = sp.add_parser("create", help="upload footage and create HeyGen digital twin")
    c.add_argument("--footage", required=True, help="motion take path")
    c.add_argument("--name", help="twin display name")
    c.add_argument("--project")
    c.set_defaults(func=cmd_create)
    cons = sp.add_parser("consent", help="request consent URL or mark local consent granted")
    cons.add_argument("--group-id")
    cons.add_argument("--mark-granted", action="store_true")
    cons.add_argument("--project")
    cons.set_defaults(func=cmd_consent)
    looks = sp.add_parser("looks", help="generate additional looks (prompt)")
    looks.add_argument("--prompt", required=True)
    looks.add_argument("--project")
    looks.set_defaults(func=cmd_looks)
