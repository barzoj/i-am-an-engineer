"""API backends with mocked httpx — no real network, no keys."""
from __future__ import annotations

import json

import httpx

from i_am_an_engineer.backends.elevenlabs import ElevenLabsClient
from i_am_an_engineer.backends.fal import FalClient
from i_am_an_engineer.backends.heygen import HeyGenClient


def _heygen_handler(request: httpx.Request) -> httpx.Response:
    path = request.url.path
    if path.endswith("/v1/asset"):
        return httpx.Response(200, json={"data": {"asset_id": "asset_1"}})
    if path.endswith("/v3/avatars"):
        return httpx.Response(
            200,
            json={
                "data": {
                    "avatar_group_id": "grp_1",
                    "look_id": "look_1",
                    "default_voice_id": "voice_1",
                    "status": "pending",
                }
            },
        )
    if "/consent" in path:
        return httpx.Response(200, json={"data": {"consent_url": "https://heygen.test/consent"}})
    if path.endswith("/v3/videos"):
        return httpx.Response(200, json={"data": {"video_id": "vid_1", "status": "pending"}})
    if "/v3/videos/" in path:
        return httpx.Response(
            200, json={"data": {"status": "completed", "video_url": "https://cdn.test/a.mp4"}}
        )
    return httpx.Response(404, json={"error": path})


def test_heygen_twin_and_aroll(tmp_path):
    footage = tmp_path / "t.mp4"
    footage.write_bytes(b"fake")
    transport = httpx.MockTransport(_heygen_handler)
    client = HeyGenClient(api_key="test-key", transport=transport)
    asset = client.upload_asset(footage)
    assert asset == "asset_1"
    twin = client.create_digital_twin(asset, name="Founder")
    assert twin.avatar_group_id == "grp_1"
    assert twin.default_voice_id == "voice_1"
    consent = client.request_consent("grp_1")
    assert "consent" in consent["consent_url"]
    job = client.create_avatar_video(
        avatar_id="look_1", script="Hello", voice_id="voice_1", aspect_ratio="9:16"
    )
    assert job.video_id == "vid_1"
    done = client.get_video("vid_1")
    assert done.status == "completed"


def test_elevenlabs_clone_and_tts(tmp_path):
    sample = tmp_path / "a.wav"
    sample.write_bytes(b"RIFF....")

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/v1/voices/add"):
            return httpx.Response(200, json={"voice_id": "el_1"})
        if "/v1/text-to-speech/" in request.url.path:
            return httpx.Response(200, content=b"ID3fakeaudio")
        return httpx.Response(404)

    client = ElevenLabsClient(api_key="el-test", transport=httpx.MockTransport(handler))
    cloned = client.clone_instant([sample], name="founder")
    assert cloned.voice_id == "el_1"
    audio = client.tts("Hello world", "el_1")
    assert audio.startswith(b"ID3")


def test_fal_submit_and_wait(tmp_path):
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path.endswith("/fal-ai/veo3.1") and request.method == "POST":
            return httpx.Response(200, json={"request_id": "req_1"})
        if path.endswith("/status"):
            calls["n"] += 1
            status = "COMPLETED" if calls["n"] > 1 else "IN_PROGRESS"
            return httpx.Response(200, json={"status": status})
        if path.endswith("/requests/req_1"):
            return httpx.Response(
                200, json={"video": {"url": "https://cdn.test/broll.mp4"}}
            )
        if path == "/broll.mp4" or str(request.url).endswith("broll.mp4"):
            return httpx.Response(200, content=b"\x00\x00fake")
        return httpx.Response(404, json={"path": path})

    client = FalClient(api_key="fal-test", transport=httpx.MockTransport(handler), sleep=lambda _s: None)
    submitted = client.submit("fal-ai/veo3.1", {"prompt": "desk"})
    assert submitted["request_id"] == "req_1"
    result = client.wait("fal-ai/veo3.1", "req_1", timeout_s=5, interval_s=0)
    assert result["video"]["url"].endswith("broll.mp4")
