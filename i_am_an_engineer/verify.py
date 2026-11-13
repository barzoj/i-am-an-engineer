"""Cheap/free authenticated key checks (no generation spend).

  iae heygen key verify       → GET /v3/users/me
  iae elevenlabs key verify   → GET /v1/user
  iae fal key verify          → GET /v1/account/billing?expand=credits
"""
from __future__ import annotations

from typing import Any

import httpx

from i_am_an_engineer.common import die
from i_am_an_engineer.keys import SERVICES, get_service, key_status, resolve_key

VERIFY_ENDPOINTS = {
    "heygen": {
        "method": "GET",
        "url": "https://api.heygen.com/v3/users/me",
        "docs": "https://developers.heygen.com/docs/api-key",
        "cost": "free account lookup",
    },
    "elevenlabs": {
        "method": "GET",
        "url": "https://api.elevenlabs.io/v1/user",
        "docs": "https://elevenlabs.io/docs/api-reference/user/get",
        "cost": "free user lookup",
    },
    "fal": {
        "method": "GET",
        "url": "https://api.fal.ai/v1/account/billing",
        "params": {"expand": "credits"},
        "docs": "https://fal.ai/docs/platform-apis/v1/account/billing",
        "cost": "free billing/credits lookup (needs billing:usage:read or READONLY/FULL key)",
    },
}


def _headers(service: str, api_key: str) -> dict[str, str]:
    if service == "heygen":
        return {"X-Api-Key": api_key, "Accept": "application/json"}
    if service == "elevenlabs":
        return {"xi-api-key": api_key, "Accept": "application/json"}
    if service == "fal":
        return {"Authorization": f"Key {api_key}", "Accept": "application/json"}
    return {"Authorization": f"Bearer {api_key}", "Accept": "application/json"}


def _summarize(service: str, body: Any, status_code: int) -> dict[str, Any]:
    summary: dict[str, Any] = {"http_status": status_code}
    if not isinstance(body, dict):
        return summary
    if service == "heygen":
        data = body.get("data") if isinstance(body.get("data"), dict) else body
        summary["billing_type"] = data.get("billing_type")
        for field in ("wallet", "subscription", "usage_based"):
            if field in data:
                summary[field] = data[field]
        if data.get("email"):
            summary["email"] = data.get("email")
        if data.get("username"):
            summary["username"] = data.get("username")
    elif service == "elevenlabs":
        sub = body.get("subscription") if isinstance(body.get("subscription"), dict) else {}
        summary["user_id"] = body.get("user_id")
        summary["subscription_tier"] = sub.get("tier") or sub.get("plan")
        summary["character_count"] = sub.get("character_count")
        summary["character_limit"] = sub.get("character_limit")
    elif service == "fal":
        summary["username"] = body.get("username")
        credits = body.get("credits") if isinstance(body.get("credits"), dict) else None
        if credits:
            summary["credits_balance"] = credits.get("current_balance")
            summary["currency"] = credits.get("currency")
    return summary


def verify_service(
    name: str,
    *,
    api_key: str | None = None,
    transport: httpx.BaseTransport | None = None,
    client: httpx.Client | None = None,
) -> dict[str, Any]:
    """Hit a free authenticated endpoint. Returns a JSON-serializable result dict."""
    if name not in VERIFY_ENDPOINTS:
        die(
            f"key verify not supported for {name!r}; "
            f"supported: {', '.join(VERIFY_ENDPOINTS)}"
        )
    svc = get_service(name)
    meta = VERIFY_ENDPOINTS[name]
    key = api_key if api_key is not None else resolve_key(svc, required=False)
    st = key_status(svc)
    result: dict[str, Any] = {
        "service": name,
        "ok": False,
        "present": bool(key),
        "source": st.get("source"),
        "masked": st.get("key"),
        "endpoint": meta["url"],
        "cost": meta["cost"],
        "docs": meta["docs"],
    }
    if not key:
        result["error"] = f"no {name} key stored; create at {svc.docs_url} then `iae {name} key set`"
        return result

    owns_client = client is None
    http = client or httpx.Client(timeout=30.0, transport=transport)
    try:
        r = http.request(
            meta["method"],
            meta["url"],
            headers=_headers(name, key),
            params=meta.get("params"),
        )
        try:
            body: Any = r.json() if r.content else {}
        except Exception:  # noqa: BLE001
            body = {"raw": r.text[:500]}
        result["summary"] = _summarize(name, body, r.status_code)
        if r.status_code == 200:
            result["ok"] = True
            result["message"] = "key valid"
        elif name == "fal" and r.status_code == 403:
            # Key authenticated but missing billing scope — still proves the secret works.
            result["ok"] = True
            result["message"] = (
                "key authenticates but lacks billing:usage:read "
                "(use READONLY/FULL/BILLING preset for balance; API preset is fine for Veo)"
            )
            result["summary"]["note"] = "403 on billing; key not rejected as invalid"
        elif r.status_code in (401, 403):
            result["error"] = f"auth failed HTTP {r.status_code}"
            result["message"] = "key rejected"
        elif 200 <= r.status_code < 300:
            result["ok"] = True
            result["message"] = "key valid"
        else:
            result["error"] = f"unexpected HTTP {r.status_code}"
            result["message"] = "verify inconclusive"
    except httpx.HTTPError as e:
        result["error"] = str(e)
        result["message"] = "network error during verify"
    finally:
        if owns_client:
            http.close()
    return result


def verify_all(
    *,
    only_present: bool = True,
    transport: httpx.BaseTransport | None = None,
) -> dict[str, Any]:
    rows = []
    for name in SERVICES:
        if name not in VERIFY_ENDPOINTS:
            st = key_status(name)
            rows.append(
                {
                    "service": name,
                    "ok": None,
                    "present": st["present"],
                    "source": st.get("source"),
                    "masked": st.get("key"),
                    "message": "verify not implemented",
                }
            )
            continue
        if only_present and not key_status(name)["present"]:
            rows.append(
                {
                    "service": name,
                    "ok": None,
                    "present": False,
                    "message": "not set — skipped",
                    "docs": get_service(name).docs_url,
                }
            )
            continue
        rows.append(verify_service(name, transport=transport))
    return {
        "keys": rows,
        "ok": all(r.get("ok") is not False or not r.get("present") for r in rows),
        "note": "verify uses free account endpoints only — no twin/TTS/B-roll spend",
    }
