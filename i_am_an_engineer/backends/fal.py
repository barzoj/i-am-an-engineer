"""fal B-roll backend (Veo 3.1 first).

Docs: https://fal.ai/models/fal-ai/veo3.1
"""
from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Callable

import httpx

from i_am_an_engineer.backends.base import BrollBackend, BrollClip, registry
from i_am_an_engineer.keys import get_service, resolve_key

QUEUE = "https://queue.fal.run"
DEFAULT_MODEL = "fal-ai/veo3.1"
DEFAULT_TIMEOUT = 120.0


class FalClient:
    def __init__(
        self,
        api_key: str | None = None,
        *,
        queue_url: str = QUEUE,
        transport: httpx.BaseTransport | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.api_key = api_key or resolve_key("fal")
        self.queue_url = queue_url.rstrip("/")
        self.sleep = sleep
        self._client = httpx.Client(
            headers={
                "Authorization": f"Key {self.api_key}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            timeout=DEFAULT_TIMEOUT,
            transport=transport,
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> FalClient:
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    def submit(self, model: str, payload: dict[str, Any]) -> dict[str, Any]:
        r = self._client.post(f"{self.queue_url}/{model}", json=payload)
        r.raise_for_status()
        return r.json()

    def status(self, model: str, request_id: str) -> dict[str, Any]:
        r = self._client.get(f"{self.queue_url}/{model}/requests/{request_id}/status")
        r.raise_for_status()
        return r.json()

    def result(self, model: str, request_id: str) -> dict[str, Any]:
        r = self._client.get(f"{self.queue_url}/{model}/requests/{request_id}")
        r.raise_for_status()
        return r.json()

    def wait(self, model: str, request_id: str, *, timeout_s: float = 600, interval_s: float = 3) -> dict[str, Any]:
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            st = self.status(model, request_id)
            status = str(st.get("status") or "").upper()
            if status in {"COMPLETED", "OK", "SUCCESS"}:
                return self.result(model, request_id)
            if status in {"FAILED", "ERROR"}:
                raise RuntimeError(f"fal job failed: {st}")
            self.sleep(interval_s)
        raise TimeoutError(f"fal job {request_id} timed out")


class FalBrollBackend(BrollBackend):
    name = "fal"

    def __init__(self, client: FalClient | None = None) -> None:
        self._client = client

    @property
    def client(self) -> FalClient:
        if self._client is None:
            self._client = FalClient()
        return self._client

    def status(self) -> dict[str, Any]:
        from i_am_an_engineer.keys import key_status

        st = key_status(get_service("fal"))
        return {
            "name": self.name,
            "role": "broll",
            "configured": bool(st["present"]),
            "key_present": bool(st["present"]),
            "key_source": st.get("source"),
            "default_model": DEFAULT_MODEL,
        }

    def generate(
        self,
        prompt: str,
        *,
        duration_s: float = 5,
        model: str = DEFAULT_MODEL,
        out_dir: Path,
        with_audio: bool = True,
    ) -> BrollClip:
        payload = {
            "prompt": prompt,
            "duration": str(int(duration_s)),
            "generate_audio": with_audio,
            "resolution": "1080p",
        }
        submitted = self.client.submit(model, payload)
        request_id = str(submitted.get("request_id") or submitted.get("requestId") or "")
        if not request_id:
            raise RuntimeError(f"fal submit missing request_id: {submitted}")
        result = self.client.wait(model, request_id)
        video = (result.get("video") or {})
        url = video.get("url") if isinstance(video, dict) else None
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path: Path | None = None
        if url:
            out_path = out_dir / f"broll_{request_id}.mp4"
            r = self.client._client.get(url)
            r.raise_for_status()
            out_path.write_bytes(r.content)
        return BrollClip(
            path=out_path,
            prompt=prompt,
            duration_s=duration_s,
            model=model,
            job_id=request_id,
            url=url,
            raw=result,
        )


registry.register("fal", FalBrollBackend)
