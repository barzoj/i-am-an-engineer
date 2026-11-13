"""ElevenLabs voice clone + TTS/STS backend.

Docs: https://elevenlabs.io/docs/
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import httpx

from i_am_an_engineer.backends.base import VoiceBackend, VoiceCloneResult, registry
from i_am_an_engineer.keys import get_service, resolve_key

API_BASE = "https://api.elevenlabs.io"
DEFAULT_TIMEOUT = 60.0


class ElevenLabsClient:
    def __init__(
        self,
        api_key: str | None = None,
        *,
        base_url: str = API_BASE,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.api_key = api_key or resolve_key("elevenlabs")
        self.base_url = base_url.rstrip("/")
        self._client = httpx.Client(
            base_url=self.base_url,
            headers={
                "xi-api-key": self.api_key or "",
                "Accept": "application/json",
            },
            timeout=DEFAULT_TIMEOUT,
            transport=transport,
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> ElevenLabsClient:
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    def request(self, method: str, path: str, **kwargs) -> httpx.Response:
        r = self._client.request(method, path, **kwargs)
        r.raise_for_status()
        return r

    def clone_instant(self, samples: list[Path], *, name: str, description: str = "") -> VoiceCloneResult:
        files = [("files", (p.name, p.read_bytes(), "audio/mpeg")) for p in samples]
        data = {"name": name}
        if description:
            data["description"] = description
        r = self.request("POST", "/v1/voices/add", data=data, files=files)
        body = r.json()
        return VoiceCloneResult(
            voice_id=str(body.get("voice_id") or body.get("id")),
            provider="elevenlabs",
            status="ready",
            raw=body,
        )

    def tts(self, text: str, voice_id: str, *, model_id: str = "eleven_multilingual_v2") -> bytes:
        r = self.request(
            "POST",
            f"/v1/text-to-speech/{voice_id}",
            headers={"Accept": "audio/mpeg"},
            json={"text": text, "model_id": model_id},
        )
        return r.content

    def sts(self, audio: Path, voice_id: str) -> bytes:
        files = {"audio": (audio.name, audio.read_bytes(), "audio/mpeg")}
        r = self.request(
            "POST",
            f"/v1/speech-to-speech/{voice_id}",
            headers={"Accept": "audio/mpeg"},
            files=files,
        )
        return r.content


class ElevenLabsVoiceBackend(VoiceBackend):
    name = "elevenlabs"

    def __init__(self, client: ElevenLabsClient | None = None) -> None:
        self._client = client

    @property
    def client(self) -> ElevenLabsClient:
        if self._client is None:
            self._client = ElevenLabsClient()
        return self._client

    def status(self) -> dict[str, Any]:
        from i_am_an_engineer.keys import key_status

        st = key_status(get_service("elevenlabs"))
        return {
            "name": self.name,
            "role": "voice",
            "configured": bool(st["present"]),
            "key_present": bool(st["present"]),
            "key_source": st.get("source"),
        }

    def clone_instant(self, samples: list[Path], *, name: str) -> VoiceCloneResult:
        return self.client.clone_instant(samples, name=name)

    def tts(self, text: str, voice_id: str, out: Path) -> Path:
        audio = self.client.tts(text, voice_id)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(audio)
        return out

    def sts(self, audio: Path, voice_id: str, out: Path) -> Path:
        data = self.client.sts(audio, voice_id)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(data)
        return out


registry.register("elevenlabs", ElevenLabsVoiceBackend)
