"""Download + normalize founder phone recordings (iPhone .mov HEVC/HDR/VFR/rotation).

Primary path: AirDrop / upload of a raw iPhone recording → SDR H.264 CFR MP4 with
rotation baked in and audio kept.
"""
from __future__ import annotations

import json
import re
import tempfile
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import httpx

from i_am_an_engineer.common import die, ensure_dir, run, which

VIDEO_EXT = {".mp4", ".mov", ".webm", ".mkv", ".m4v"}
AUDIO_EXT = {".wav", ".m4a", ".mp3", ".aac", ".caf"}
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp", ".heic"}
MEDIA_EXT = VIDEO_EXT | AUDIO_EXT | IMAGE_EXT

# Target for twin/compose-friendly masters.
DEFAULT_FPS = 30
DEFAULT_AUDIO_HZ = 48000


def is_url(value: str) -> bool:
    try:
        u = urlparse(value)
    except Exception:  # noqa: BLE001
        return False
    return u.scheme in {"http", "https"} and bool(u.netloc)


def resolve_share_url(url: str) -> str:
    """Best-effort rewrite of common cloud share links to a direct-ish download URL.

    Google Drive file links are rewritten to the uc?export=download form.
    iCloud share links are returned as-is (often still need a browser session —
    we try a plain GET with redirects and surface a clear error if HTML comes back).
    """
    u = urlparse(url)
    host = (u.netloc or "").lower()
    if "drive.google.com" in host:
        # /file/d/<id>/view or /open?id=<id>
        m = re.search(r"/file/d/([^/]+)", u.path or "")
        file_id = m.group(1) if m else None
        if not file_id:
            qs = parse_qs(u.query or "")
            file_id = (qs.get("id") or [None])[0]
        if file_id:
            return f"https://drive.google.com/uc?export=download&id={file_id}"
    if "docs.google.com" in host and "/uc" in (u.path or ""):
        return url
    # iCloud: keep original; download() follows redirects.
    return url


def guess_filename_from_url(url: str, content_type: str | None = None) -> str:
    path = urlparse(url).path or ""
    name = Path(path).name
    if name and "." in name and not name.endswith("/"):
        return name
    if content_type:
        ct = content_type.split(";")[0].strip().lower()
        mapping = {
            "video/quicktime": "recording.mov",
            "video/mp4": "recording.mp4",
            "audio/mp4": "recording.m4a",
            "audio/mpeg": "recording.mp3",
            "audio/wav": "recording.wav",
            "image/jpeg": "still.jpg",
            "image/png": "still.png",
        }
        if ct in mapping:
            return mapping[ct]
    return "download.bin"


def download_url(url: str, dest_dir: Path, *, timeout: float = 120.0) -> Path:
    """Download http(s) media (incl. rewritten Drive links) into dest_dir."""
    ensure_dir(dest_dir)
    final_url = resolve_share_url(url)
    with httpx.Client(follow_redirects=True, timeout=timeout) as client:
        with client.stream("GET", final_url) as resp:
            resp.raise_for_status()
            ctype = resp.headers.get("content-type", "")
            # Google Drive virus-scan interstitial sometimes returns HTML/confirm cookie.
            if "text/html" in ctype.lower():
                # Try confirm token pattern once.
                body_preview = b"".join(resp.iter_bytes(chunk_size=65536))
                text = body_preview.decode("utf-8", errors="replace")
                conf = re.search(r"confirm=([0-9A-Za-z_]+)", text)
                fid = re.search(r"[?&]id=([0-9A-Za-z_-]+)", final_url)
                if conf and fid:
                    confirm_url = (
                        f"https://drive.google.com/uc?export=download"
                        f"&confirm={conf.group(1)}&id={fid.group(1)}"
                    )
                    return download_url(confirm_url, dest_dir, timeout=timeout)
                die(
                    "download returned HTML (share link may need a public 'anyone with the link' "
                    "permission, or iCloud requires a browser). Pass a direct file URL or a local path."
                )
            name = guess_filename_from_url(final_url, ctype)
            # Content-Disposition filename=
            cd = resp.headers.get("content-disposition") or ""
            m = re.search(r'filename\*?=(?:UTF-8\'\')?"?([^";]+)"?', cd, re.I)
            if m:
                name = Path(m.group(1).strip()).name or name
            out = dest_dir / name
            with out.open("wb") as f:
                for chunk in resp.iter_bytes():
                    f.write(chunk)
    if out.stat().st_size == 0:
        die(f"downloaded empty file from {url}")
    return out


def probe_json(path: Path) -> dict:
    if not which("ffprobe"):
        return {}
    r = run(
        [
            "ffprobe",
            "-v",
            "quiet",
            "-print_format",
            "json",
            "-show_format",
            "-show_streams",
            "-show_entries",
            "stream_side_data:stream=index,codec_name,codec_type,width,height,pix_fmt,color_space,color_transfer,color_primaries,avg_frame_rate,r_frame_rate,rotation:stream_tags=rotate",
            str(path),
        ],
        check=True,
    )
    return json.loads(r.stdout or "{}")


def _has_zscale() -> bool:
    if not which("ffmpeg"):
        return False
    try:
        r = run(["ffmpeg", "-hide_banner", "-filters"], check=False)
        return "zscale" in (r.stdout or "")
    except SystemExit:
        return False


def build_normalize_vf(*, fps: int = DEFAULT_FPS, hdr: bool = False) -> str:
    """Video filter graph: CFR + SDR yuv420p. Rotation is applied by the encoder from metadata."""
    parts: list[str] = []
    if hdr and _has_zscale():
        # Hable tonemap → BT.709 SDR
        parts.append(
            "zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,"
            "tonemap=tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p"
        )
    else:
        parts.append("format=yuv420p")
    parts.append(f"fps={fps}")
    # Even dimensions for libx264
    parts.append("scale=trunc(iw/2)*2:trunc(ih/2)*2")
    return ",".join(parts)


def looks_hdr(probe: dict) -> bool:
    for stream in probe.get("streams") or []:
        if stream.get("codec_type") != "video":
            continue
        trc = str(stream.get("color_transfer") or "").lower()
        prim = str(stream.get("color_primaries") or "").lower()
        if any(x in trc for x in ("smpte2084", "arib-std-b67", "bt2020")):
            return True
        if "bt2020" in prim:
            return True
        # Dolby Vision side data often present as DOVI in codec tags / side_data
        for sd in stream.get("side_data_list") or []:
            if "dolby" in json.dumps(sd).lower() or "dovi" in json.dumps(sd).lower():
                return True
    return False


def is_video(path: Path) -> bool:
    return path.suffix.lower() in VIDEO_EXT


def normalize_video(
    src: Path,
    dest: Path,
    *,
    fps: int = DEFAULT_FPS,
    audio_hz: int = DEFAULT_AUDIO_HZ,
) -> dict:
    """Re-encode to SDR H.264 CFR MP4; bake rotation; keep audio as AAC.

    Returns metadata about the normalize step.
    """
    if not which("ffmpeg"):
        die("ffmpeg not found on PATH (required to normalize iPhone .mov / HEVC)")
    ensure_dir(dest.parent)
    probe = probe_json(src)
    hdr = looks_hdr(probe)
    vf = build_normalize_vf(fps=fps, hdr=hdr)
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(src),
        "-map",
        "0:v:0",
        "-map",
        "0:a:0?",
        "-vf",
        vf,
        "-c:v",
        "libx264",
        "-preset",
        "fast",
        "-crf",
        "18",
        "-pix_fmt",
        "yuv420p",
        "-colorspace",
        "bt709",
        "-color_primaries",
        "bt709",
        "-color_trc",
        "bt709",
        "-fps_mode",
        "cfr",
        "-r",
        str(fps),
        "-c:a",
        "aac",
        "-ar",
        str(audio_hz),
        "-b:a",
        "192k",
        "-ac",
        "2",
        # Clear rotate tag after baking orientation into pixels (ffmpeg applies displaymatrix on encode).
        "-metadata:s:v:0",
        "rotate=0",
        "-movflags",
        "+faststart",
        str(dest),
    ]
    r = run(cmd, check=False)
    if r.returncode != 0:
        # Retry without audio map if source has no audio
        cmd_no_a = [
            "ffmpeg",
            "-y",
            "-i",
            str(src),
            "-map",
            "0:v:0",
            "-vf",
            vf,
            "-c:v",
            "libx264",
            "-preset",
            "fast",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            "-colorspace",
            "bt709",
            "-color_primaries",
            "bt709",
            "-color_trc",
            "bt709",
            "-fps_mode",
            "cfr",
            "-r",
            str(fps),
            "-an",
            "-metadata:s:v:0",
            "rotate=0",
            "-movflags",
            "+faststart",
            str(dest),
        ]
        run(cmd_no_a, check=True)
        audio_kept = False
    else:
        audio_kept = True
        # Detect if output has audio
        out_probe = probe_json(dest)
        audio_kept = any(s.get("codec_type") == "audio" for s in out_probe.get("streams") or [])
    return {
        "source": str(src),
        "normalized": str(dest),
        "hdr_tonemapped": hdr,
        "fps": fps,
        "audio_kept": audio_kept,
        "video_codec": "libx264",
        "pix_fmt": "yuv420p",
        "color": "bt709",
    }


def materialize_input(value: str, scratch: Path) -> Path:
    """Resolve a local path/glob-already-resolved path or URL to a local file."""
    if is_url(value):
        return download_url(value, ensure_dir(scratch / "downloads"))
    p = Path(value).expanduser()
    if not p.is_file():
        die(f"input not found: {value}")
    return p.resolve()


def make_synthetic_clip(
    dest: Path,
    *,
    seconds: float = 1.0,
    width: int = 320,
    height: int = 240,
    fps: int = 30,
    rotate_metadata: bool = False,
) -> Path:
    """Tiny solid-color test clip (no faces). Used for normalize tests — not for ASR dry-run."""
    if not which("ffmpeg"):
        die("ffmpeg required to generate synthetic test clip")
    ensure_dir(dest.parent)
    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "lavfi",
        "-i",
        f"color=c=blue:s={width}x{height}:d={seconds}:r={fps}",
        "-f",
        "lavfi",
        "-i",
        f"sine=frequency=440:duration={seconds}",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-shortest",
        str(dest),
    ]
    if rotate_metadata:
        # Simulate an iPhone portrait tag without real phone media.
        cmd[-1:-1] = ["-metadata:s:v:0", "rotate=90"]
    run(cmd, check=True)
    return dest


def make_spoken_sample(
    dest: Path,
    *,
    text: str = (
        "Most founders cannot deliver a calm confident take on camera. "
        "Record once. Train your digital twin. Then cut a professional English ad."
    ),
    width: int = 1280,
    height: int = 720,
    fps: int = 30,
) -> Path:
    """Realistic acceptance sample: solid color + espeak-ng English TTS (no faces).

    Requires ffmpeg and espeak-ng. Dry-run captions are burned from ASR of this audio.
    Synthetic samples are for dry-run only — never train a HeyGen twin on them.
    """
    if not which("ffmpeg"):
        die("ffmpeg required to generate spoken sample")
    if not which("espeak-ng") and not which("espeak"):
        die("espeak-ng (or espeak) required for spoken acceptance sample")
    ensure_dir(dest.parent)
    import tempfile

    espeak = which("espeak-ng") or which("espeak")
    with tempfile.TemporaryDirectory() as td:
        wav = Path(td) / "tts.wav"
        run([espeak, "-v", "en-us", "-w", str(wav), text], check=True)
        # Probe duration from wav via ffprobe when possible; else let -shortest trim.
        cmd = [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"color=c=0x1a1a2e:s={width}x{height}:r={fps}",
            "-i",
            str(wav),
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-shortest",
            "-movflags",
            "+faststart",
            str(dest),
        ]
        run(cmd, check=True)
    return dest
