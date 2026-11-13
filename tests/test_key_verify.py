"""Mocked key verify + doctor --keys (no real network)."""
from __future__ import annotations

import json
import os
from types import SimpleNamespace

import httpx
import pytest

from i_am_an_engineer import doctor as doctor_mod
from i_am_an_engineer.keys import cmd_key
from i_am_an_engineer.verify import verify_all, verify_service


def _router(request: httpx.Request) -> httpx.Response:
    host = request.url.host
    path = request.url.path
    auth = request.headers.get("x-api-key") or request.headers.get("xi-api-key") or request.headers.get(
        "authorization", ""
    )
    if "bad" in auth.lower() or auth.endswith("invalid"):
        return httpx.Response(401, json={"error": "unauthorized"})

    if host == "api.heygen.com" and path.endswith("/v3/users/me"):
        return httpx.Response(
            200,
            json={
                "data": {
                    "email": "founder@example.com",
                    "billing_type": "wallet",
                    "wallet": {"balance": 12.5, "currency": "USD"},
                }
            },
        )
    if host == "api.elevenlabs.io" and path.endswith("/v1/user"):
        return httpx.Response(
            200,
            json={
                "user_id": "u1",
                "subscription": {
                    "tier": "creator",
                    "character_count": 100,
                    "character_limit": 121000,
                },
            },
        )
    if host == "api.fal.ai" and path.endswith("/v1/account/billing"):
        # Simulate API-preset key without billing scope when Authorization ends with :api
        if auth.endswith(":api"):
            return httpx.Response(403, json={"error": {"type": "authorization_error", "message": "missing scope"}})
        return httpx.Response(
            200,
            json={"username": "team", "credits": {"current_balance": 10.0, "currency": "USD"}},
        )
    return httpx.Response(404, json={"error": f"{host}{path}"})


@pytest.fixture()
def transport():
    return httpx.MockTransport(_router)


def test_verify_heygen_ok(transport, monkeypatch):
    monkeypatch.setenv("HEYGEN_API_KEY", "hg-test-key-abcdefghijklmnop")
    r = verify_service("heygen", transport=transport)
    assert r["ok"] is True
    assert r["summary"]["billing_type"] == "wallet"
    assert r["cost"].startswith("free")


def test_verify_elevenlabs_ok(transport, monkeypatch):
    monkeypatch.setenv("ELEVENLABS_API_KEY", "el-test-key-abcdefghijklmnop")
    r = verify_service("elevenlabs", transport=transport)
    assert r["ok"] is True
    assert r["summary"]["subscription_tier"] == "creator"


def test_verify_fal_ok_and_403_still_ok(transport, monkeypatch):
    monkeypatch.setenv("FAL_KEY", "fal-test-key-abcdefghijklmnop")
    r = verify_service("fal", transport=transport)
    assert r["ok"] is True
    assert r["summary"]["credits_balance"] == 10.0

    monkeypatch.setenv("FAL_KEY", "fal-test-key:api")
    r2 = verify_service("fal", transport=transport)
    assert r2["ok"] is True
    assert "billing" in (r2.get("message") or "").lower() or "403" in str(r2.get("summary"))


def test_verify_rejects_bad_key(transport, monkeypatch):
    monkeypatch.setenv("HEYGEN_API_KEY", "bad-invalid")
    r = verify_service("heygen", transport=transport)
    assert r["ok"] is False
    assert r["summary"]["http_status"] == 401


def test_verify_missing_key(monkeypatch):
    monkeypatch.setattr(
        "i_am_an_engineer.verify.resolve_key",
        lambda *a, **k: None,
    )
    monkeypatch.setattr(
        "i_am_an_engineer.verify.key_status",
        lambda *a, **k: {"service": "heygen", "present": False, "source": None, "key": None},
    )
    r = verify_service("heygen")
    assert r["ok"] is False
    assert r["present"] is False


def test_cmd_key_verify_json(transport, monkeypatch, capsys):
    monkeypatch.setenv("HEYGEN_API_KEY", "hg-test-key-abcdefghijklmnop")

    # Patch verify_service to use our transport via monkeypatch of httpx.Client
    real_client = httpx.Client

    class Client(real_client):
        def __init__(self, *a, **k):
            k["transport"] = transport
            super().__init__(*a, **k)

    monkeypatch.setattr(httpx, "Client", Client)
    cmd_key("heygen", "verify", as_json=True)
    out = json.loads(capsys.readouterr().out)
    assert out["ok"] is True


def test_doctor_keys_mocked(transport, monkeypatch, capsys):
    monkeypatch.setenv("HEYGEN_API_KEY", "hg-test-key-abcdefghijklmnop")
    monkeypatch.setenv("ELEVENLABS_API_KEY", "el-test-key-abcdefghijklmnop")
    monkeypatch.setenv("FAL_KEY", "fal-test-key-abcdefghijklmnop")
    for k in ("DEEPINFRA_API_KEY",):
        monkeypatch.delenv(k, raising=False)

    real_client = httpx.Client

    class Client(real_client):
        def __init__(self, *a, **k):
            k["transport"] = transport
            super().__init__(*a, **k)

    monkeypatch.setattr(httpx, "Client", Client)
    doctor_mod.cmd_doctor(SimpleNamespace(project=None, json=False, keys=True))
    text = capsys.readouterr().out
    assert "verify OK" in text
    assert "keys" in text.lower() or "key heygen" in text
