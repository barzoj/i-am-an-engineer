"""HeyGen official API backend (digital twin + A-roll + optional TTS).

Docs: https://developers.heygen.com/
Uses API key from `iae heygen key set` / HEYGEN_API_KEY.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Callable

import httpx

from i_am_an_engineer.backends.base import (
    TwinBackend,
    TwinCreateResult,
    VideoJob,
    VoiceBackend,
    VoiceCloneResult,
    registry,
)
from i_am_an_engineer.keys import get_service, resolve_key

API_BASE = "https://api.heygen.com"
DEFAULT_TIMEOUT = 60.0


class HeyGenClient:
    def __init__(
        self,
        api_key: str | None = None,
        *,
        base_url: str = API_BASE,
        transport: httpx.BaseTransport | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.api_key = api_key or resolve_key("heygen")
        self.base_url = base_url.rstrip("/")
        self.sleep = sleep
        self._client = httpx.Client(
            base_url=self.base_url,
            headers={
                "X-Api-Key": self.api_key or "",
                "Accept": "application/json",
            },
            timeout=DEFAULT_TIMEOUT,
            transport=transport,
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> HeyGenClient:
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    def request(self, method: str, path: str, **kwargs) -> dict[str, Any]:
        r = self._client.request(method, path, **kwargs)
        r.raise_for_status()
        if not r.content:
            return {}
        data = r.json()
        return data if isinstance(data, dict) else {"data": data}

    def upload_asset(self, path: Path) -> str:
        """Upload training footage; returns asset_id."""
        content = path.read_bytes()
        # Official flow uses POST /v3/assets or direct S3; we use multipart asset create.
        files = {"file": (path.name, content, "video/mp4")}
        data = self.request("POST", "/v1/asset", files=files)
        asset = (data.get("data") or data)
        asset_id = asset.get("asset_id") or asset.get("id")
        if not asset_id:
            raise RuntimeError(f"HeyGen asset upload missing id: {data}")
        return str(asset_id)

    def create_digital_twin(self, asset_id: str, *, name: str) -> TwinCreateResult:
        payload = {
            "name": name,
            "type": "digital_twin",
            "asset_id": asset_id,
        }
        data = self.request("POST", "/v3/avatars", json=payload)
        item = data.get("data") or data
        return TwinCreateResult(
            avatar_group_id=str(item.get("avatar_group_id") or item.get("group_id") or item.get("id")),
            look_id=(str(item["look_id"]) if item.get("look_id") else None),
            default_voice_id=(
                str(item["default_voice_id"])
                if item.get("default_voice_id")
                else (str(item["avatar_item"]["default_voice_id"]) if isinstance(item.get("avatar_item"), dict) and item["avatar_item"].get("default_voice_id") else None)
            ),
            status=str(item.get("status") or "pending"),
            raw=data,
        )

    def request_consent(self, avatar_group_id: str) -> dict[str, Any]:
        data = self.request("POST", f"/v3/avatars/{avatar_group_id}/consent")
        item = data.get("data") or data
        return {
            "consent_url": item.get("consent_url") or item.get("url"),
            "expires_in_hours": item.get("expires_in_hours", 24),
            "raw": data,
        }

    def get_look(self, look_id: str) -> dict[str, Any]:
        data = self.request("GET", f"/v3/avatars/looks/{look_id}")
        return data.get("data") or data

    def create_avatar_video(
        self,
        *,
        avatar_id: str,
        script: str,
        voice_id: str | None = None,
        aspect_ratio: str = "9:16",
        resolution: str = "1080p",
        engine: str = "avatar_v",
    ) -> VideoJob:
        engine_body: dict[str, Any] = {}
        if engine == "avatar_v":
            engine_body = {"type": "avatar_v"}
        payload: dict[str, Any] = {
            "type": "avatar",
            "avatar_id": avatar_id,
            "script": script,
            "resolution": resolution,
            "aspect_ratio": aspect_ratio,
        }
        if voice_id:
            payload["voice_id"] = voice_id
        if engine_body:
            payload["engine"] = engine_body
        data = self.request("POST", "/v3/videos", json=payload)
        item = data.get("data") or data
        return VideoJob(
            video_id=str(item.get("video_id") or item.get("id")),
            status=str(item.get("status") or "pending"),
            download_url=item.get("video_url") or item.get("download_url"),
            raw=data,
        )

    def create_cinematic(self, *, script: str, avatar_id: str, aspect_ratio: str = "9:16") -> VideoJob:
        payload = {
            "type": "cinematic_avatar",
            "avatar_id": avatar_id,
            "script": script,
            "aspect_ratio": aspect_ratio,
        }
        data = self.request("POST", "/v3/videos", json=payload)
        item = data.get("data") or data
        return VideoJob(
            video_id=str(item.get("video_id") or item.get("id")),
            status=str(item.get("status") or "pending"),
            raw=data,
        )

    def get_video(self, video_id: str) -> VideoJob:
        data = self.request("GET", f"/v3/videos/{video_id}")
        item = data.get("data") or data
        return VideoJob(
            video_id=video_id,
            status=str(item.get("status") or "unknown"),
            download_url=item.get("video_url") or item.get("download_url"),
            raw=data,
        )

    def poll_video(self, video_id: str, *, timeout_s: float = 600, interval_s: float = 5) -> VideoJob:
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            job = self.get_video(video_id)
            if job.status.lower() in {"completed", "success", "done"}:
                return job
            if job.status.lower() in {"failed", "error", "fail"}:
                raise RuntimeError(f"HeyGen video failed: {json.dumps(job.raw)[:500]}")
            self.sleep(interval_s)
        raise TimeoutError(f"HeyGen video {video_id} not ready after {timeout_s}s")

    def tts(self, text: str, voice_id: str) -> bytes:
        data = self.request(
            "POST",
            "/v3/models/audio/tts",
            json={"voice_id": voice_id, "text": text},
        )
        item = data.get("data") or data
        url = item.get("audio_url")
        if url:
            audio = self._client.get(url)
            audio.raise_for_status()
            return audio.content
        b64 = item.get("audio_base64")
        if b64:
            import base64

            return base64.b64decode(b64)
        raise RuntimeError(f"HeyGen TTS missing audio: {data}")


class HeyGenTwinBackend(TwinBackend):
    name = "heygen"

    def __init__(self, client: HeyGenClient | None = None) -> None:
        self.client = client or HeyGenClient()

    def status(self) -> dict[str, Any]:
        from i_am_an_engineer.keys import key_status

        st = key_status(get_service("heygen"))
        return {"name": self.name, "configured": st["present"], "key": st}

    def create_digital_twin(self, footage: Path, *, name: str) -> TwinCreateResult:
        asset_id = self.client.upload_asset(footage)
        return self.client.create_digital_twin(asset_id, name=name)

    def request_consent(self, avatar_group_id: str) -> dict[str, Any]:
        return self.client.request_consent(avatar_group_id)

    def poll_avatar(self, look_id: str) -> dict[str, Any]:
        return self.client.get_look(look_id)

    def render_aroll(
        self,
        *,
        avatar_id: str,
        script: str,
        voice_id: str | None,
        aspect_ratio: str,
        engine: str = "avatar_v",
        resolution: str = "1080p",
    ) -> VideoJob:
        if engine == "cinematic_avatar":
            return self.client.create_cinematic(
                script=script, avatar_id=avatar_id, aspect_ratio=aspect_ratio
            )
        return self.client.create_avatar_video(
            avatar_id=avatar_id,
            script=script,
            voice_id=voice_id,
            aspect_ratio=aspect_ratio,
            engine=engine,
            resolution=resolution,
        )

    def poll_video(self, video_id: str) -> VideoJob:
        return self.client.get_video(video_id)


class HeyGenVoiceBackend(VoiceBackend):
    name = "heygen-voice"

    def __init__(self, client: HeyGenClient | None = None) -> None:
        self.client = client or HeyGenClient()

    def status(self) -> dict[str, Any]:
        return HeyGenTwinBackend(self.client).status()

    def clone_instant(self, samples: list[Path], *, name: str) -> VoiceCloneResult:
        # Instant clone from twin footage is automatic; dedicated IVC endpoint:
        files = [("files", (p.name, p.read_bytes(), "audio/wav")) for p in samples]
        data = self.client.request(
            "POST",
            "/v3/models/audio/voices",
            data={"mode": "instant", "name": name},
            files=files,
        )
        item = data.get("data") or data
        return VoiceCloneResult(
            voice_id=str(item.get("voice_id") or item.get("id")),
            provider="heygen",
            status=str(item.get("status") or "ready"),
            raw=data,
        )

    def tts(self, text: str, voice_id: str, out: Path) -> Path:
        audio = self.client.tts(text, voice_id)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(audio)
        return out

    def sts(self, audio: Path, voice_id: str, out: Path) -> Path:
        files = {"audio": (audio.name, audio.read_bytes(), "audio/wav")}
        data = self.client.request(
            "POST",
            "/v3/models/audio/sts",
            data={"voice_id": voice_id},
            files=files,
        )
        item = data.get("data") or data
        url = item.get("audio_url")
        if not url:
            raise RuntimeError(f"HeyGen STS missing audio_url: {data}")
        content = self.client._client.get(url)
        content.raise_for_status()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(content.content)
        return out


def _factory() -> HeyGenTwinBackend:
    return HeyGenTwinBackend()


registry.register("heygen", _factory)
