"""Ingest recording takes: local paths or http(s) URLs, normalize iPhone .mov.

Primary test path: founder AirDrops / uploads a raw iPhone recording
(.mov, HEVC/H.265, often HDR/Dolby Vision 10-bit, VFR, rotation metadata).

  iae ingest ./IMG_1234.MOV --kind motion
  iae ingest https://example.com/take.mov --kind motion
  iae ingest recordings/raw/*.mp4 --kind motion --no-normalize
"""
from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from i_am_an_engineer.common import die, emit, ensure_dir, project_dir, sha256_file
from i_am_an_engineer.media import (
    MEDIA_EXT,
    is_url,
    is_video,
    materialize_input,
    normalize_video,
    probe_json,
)
from i_am_an_engineer.project import load_project


def probe(path: Path) -> dict:
    info: dict = {
        "path": str(path),
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
        "suffix": path.suffix.lower(),
    }
    ff = probe_json(path)
    if ff:
        info["ffprobe"] = ff
    return info


def _collect_inputs(values: list[str], scratch: Path) -> list[tuple[str, Path]]:
    """Return (original_ref, local_path) pairs."""
    out: list[tuple[str, Path]] = []
    for value in values:
        if is_url(value):
            out.append((value, materialize_input(value, scratch)))
            continue
        p = Path(value).expanduser()
        if p.is_file():
            out.append((value, p.resolve()))
            continue
        hits = sorted(Path().glob(value))
        if not hits:
            # also try absolute-ish from cwd with brackets etc.
            die(f"no input matched: {value}")
        for h in hits:
            if h.is_file():
                out.append((value, h.resolve()))
    if not out:
        die("no input files matched")
    return out


def ingest_one(
    root: Path,
    src: Path,
    *,
    kind: str,
    dest_dir: Path,
    source_ref: str,
    normalize: bool = True,
    force: bool = False,
    fps: int = 30,
) -> dict:
    suffix = src.suffix.lower()
    if suffix not in MEDIA_EXT and not is_url(source_ref):
        # After download, suffix should be known; allow .bin only if we still detect video via ffprobe
        if suffix not in MEDIA_EXT:
            die(f"unsupported media type: {src}")

    normalize_meta = None
    if kind in {"motion", "voice"} and is_video(src) and normalize:
        norm_dir = ensure_dir(root / "work" / "ingest" / "normalized")
        stem = src.stem
        target = dest_dir / f"{stem}.mp4"
        if target.exists() and not force:
            target = dest_dir / f"{stem}_{sha256_file(src)[:8]}.mp4"
        raw_copy = ensure_dir(root / "work" / "ingest" / "raw") / src.name
        if not raw_copy.exists() or force:
            shutil.copy2(src, raw_copy)
        normalize_meta = normalize_video(src, target, fps=fps)
        stored = target
    else:
        # stills / audio / already-normalized: copy as-is
        name = src.name
        if suffix not in MEDIA_EXT:
            name = src.name + (".mp4" if kind == "motion" else "")
        target = dest_dir / name
        if target.exists() and not force:
            target = dest_dir / f"{src.stem}_{sha256_file(src)[:8]}{src.suffix}"
        shutil.copy2(src, target)
        stored = target

    meta = probe(stored)
    meta.update(
        {
            "kind": kind,
            "ingested_at": datetime.now(timezone.utc).isoformat(),
            "source": source_ref,
            "normalized": bool(normalize_meta),
            "normalize": normalize_meta,
        }
    )
    return meta


def cmd_ingest(args) -> None:
    root = project_dir(getattr(args, "project", None))
    data = load_project(root)
    kind = args.kind
    dest_rel = (data.get("recordings") or {}).get(kind)
    if not dest_rel:
        die(f"unknown kind {kind!r}; use motion|stills|voice")
    dest = ensure_dir(root / dest_rel)
    manifest_path = root / "work" / "ingest" / "manifest.jsonl"
    ensure_dir(manifest_path.parent)
    scratch = ensure_dir(root / "work" / "ingest" / "scratch")
    pairs = _collect_inputs(list(args.files), scratch)
    written = []
    with manifest_path.open("a", encoding="utf-8") as mf:
        for source_ref, src in pairs:
            meta = ingest_one(
                root,
                src,
                kind=kind,
                dest_dir=dest,
                source_ref=source_ref,
                normalize=not getattr(args, "no_normalize", False),
                force=bool(getattr(args, "force", False)),
                fps=int(getattr(args, "fps", 30)),
            )
            mf.write(json.dumps(meta) + "\n")
            written.append(meta)
    emit({"ingested": len(written), "dest": str(dest), "items": written}, as_json=True)


def register(sub) -> None:
    import argparse

    p = sub.add_parser(
        "ingest",
        help="ingest local paths or http(s) URLs; normalize iPhone .mov to SDR H.264 CFR",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument(
        "files",
        nargs="+",
        help="local files, globs, or http(s) URLs (Drive/iCloud share links where possible)",
    )
    p.add_argument(
        "--kind",
        required=True,
        choices=["motion", "stills", "voice"],
        help="destination bucket under recordings/",
    )
    p.add_argument("--project", help="project directory (default: cwd)")
    p.add_argument("--force", action="store_true", help="overwrite same-named files")
    p.add_argument(
        "--no-normalize",
        action="store_true",
        help="copy video as-is (skip HEVC/HDR/VFR → H.264 CFR)",
    )
    p.add_argument("--fps", type=int, default=30, help="constant frame rate target (default 30)")
    p.set_defaults(func=cmd_ingest)
