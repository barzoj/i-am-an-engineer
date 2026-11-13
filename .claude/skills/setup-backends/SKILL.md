---
name: setup-backends
description: Get and store HeyGen, ElevenLabs, and fal API keys for i-am-an-engineer; document signup, wallet/plan, where to create keys, top-up, pipeline costs; verify with free account calls. Use when keys are missing, doctor fails, or before twin/A-roll/B-roll.
---

# Setup backends (get API keys)

Bootstrap first: `export PATH="$PWD/bin:$PATH"` then `iae doctor` (`bin/iae` self-bootstraps uv).

## Commands (store → verify → board)

```bash
iae doctor
iae doctor --keys                 # summary + free verify for each present key
iae backend status                # exit 0 even with no keys

iae heygen key set                # then: iae heygen key verify
iae elevenlabs key set            # then: iae elevenlabs key verify
iae fal key set                   # then: iae fal key verify

iae heygen key status
iae elevenlabs key status
iae fal key status
iae backend status
```

Env overrides (win over keyring): `HEYGEN_API_KEY`, `ELEVENLABS_API_KEY`, `FAL_KEY`.

`key verify` / `doctor --keys` call **free account endpoints only** (no twin render, no TTS, no Veo). Safe to run anytime.

---

## Get API keys (official)

Prices move — always re-check the linked official pages before large spend. Figures below are from vendor docs as of late 2026.

### 1. HeyGen API (digital twin + A-roll) — **required for twin path**

| | |
|---|---|
| Sign up | [app.heygen.com](https://app.heygen.com) / [platform.heygen.com](https://platform.heygen.com) |
| Plan / wallet | **No Creator/Pro subscription required.** API uses a **standalone PAYG USD wallet**. Web Pro does **not** fund API calls. No free API credits since Feb 2026. PAYG credits expire after **12 months**. |
| Create key | HeyGen app → **Developers** (left sidebar) → **API keys** → generate. Or [developers.heygen.com/docs/api-key](https://developers.heygen.com/docs/api-key). Copy once — you cannot view it again without regenerating. |
| Top-up | Buy **any USD amount** of API credits on the platform wallet ([API pricing help](https://help.heygen.com/en/articles/10060327-heygen-api-pricing-explained)). Self-serve prepaid wallets are commonly started from a small USD purchase (check the wallet UI). |
| Auth header | `X-Api-Key` → `https://api.heygen.com` |
| Verify (free) | `iae heygen key verify` → `GET /v3/users/me` ([docs](https://developers.heygen.com/docs/api-key)) |

**Pipeline costs (API, billed by output seconds; failed/cancelled not charged):**

| Step | What | Typical cost (self-serve) |
|---|---|---|
| Twin create | Digital twin from footage | ~**$2.13** create (see current pricing table on help article) |
| Consent | Founder likeness consent | free (product gate, not a credit burn) |
| A-roll Avatar III digital twin | `iae generate aroll` default path | **~$0.60 / min** |
| A-roll Avatar IV digital twin / studio | higher fidelity | **~$4.83 / min** |
| A-roll Avatar V digital twin | highest | **~$7.20 / min** |
| Photo-avatar Avatar IV | alternate | **~$2.31 / min** |

Official: [HeyGen API pricing explained](https://help.heygen.com/en/articles/10060327-heygen-api-pricing-explained), [API key](https://developers.heygen.com/docs/api-key). Also `knowledge/backends/heygen-api-vs-pro.md`.

**Budget tip:** a 30s Avatar III twin A-roll ≈ **$0.30**. Retries burn credits — lock script before render.

### 2. ElevenLabs (voice clone + TTS) — **recommended**

| | |
|---|---|
| Sign up | [elevenlabs.io/app/sign-up](https://elevenlabs.io/app/sign-up) |
| Plan | **API key** from any account. **Instant Voice Cloning (IVC):** Starter+ (commercial). **Professional Voice Cloning (PVC):** **Creator+**. For founder ads that need PVC quality, use **Creator or higher**. Free tier has API access but tiny credit pool. |
| Create key | [elevenlabs.io/app/settings/api-keys](https://elevenlabs.io/app/settings/api-keys) → **Create key** → copy once. Prefer a key with at least **User: Read** so verify works. |
| Top-up | Monthly plan credits (Creator ≈ **$22/mo**, 121k credits; first month often discounted) and/or usage-based / PAYG per [API pricing](https://elevenlabs.io/pricing/api). |
| Auth header | `xi-api-key` → `https://api.elevenlabs.io` |
| Verify (free) | `iae elevenlabs key verify` → `GET /v1/user` ([docs](https://elevenlabs.io/docs/api-reference/user/get)) |

**Pipeline costs (API USD rates from ElevenLabs API pricing; credits also apply on subscription plans):**

| Step | What | Typical cost |
|---|---|---|
| IVC clone | `iae voice clone` | plan entitlement (Starter+); uses library slot, not a per-char TTS burn |
| PVC | professional clone | Creator+ entitlement; longer training audio (≥30 min) |
| TTS | `iae voice tts` (Multilingual v2) | about **$0.08 / 1k characters** (API); Flash/Turbo cheaper |
| STS / voice changer | optional | about **$0.12 / min** (API) |

Official: [pricing](https://elevenlabs.io/pricing), [API pricing](https://elevenlabs.io/pricing/api), [IVC guide](https://elevenlabs.io/docs/eleven-api/guides/how-to/voices/instant-voice-cloning).

### 3. fal.ai (B-roll / Veo 3.1) — **required for generated B-roll**

| | |
|---|---|
| Sign up | [fal.ai](https://fal.ai) dashboard |
| Plan / wallet | **No subscription.** Pay-per-use credits. Account locks when balance drops below the lock threshold. |
| Create key | [fal.ai/dashboard/keys](https://fal.ai/dashboard/keys) → **Create Key**. Start with **`API` preset** for model calls. For `iae fal key verify` balance readout, prefer a key with `billing:usage:read` (**READONLY** / **FULL** / **BILLING**). |
| Top-up | Add credits in Billing. Community/docs commonly cite a **~$10 minimum** top-up — confirm in the billing UI. |
| Auth header | `Authorization: Key $FAL_KEY` → `queue.fal.run` / `api.fal.ai` |
| Verify (free) | `iae fal key verify` → `GET https://api.fal.ai/v1/account/billing?expand=credits` ([docs](https://fal.ai/docs/platform-apis/v1/account/billing)). A **403** still means the key authenticates (missing billing scope); **401** means bad key. |

**Pipeline costs (Veo 3.1 on fal, pay-per-second):**

| Step | Model | Typical cost |
|---|---|---|
| B-roll standard 720p/1080p **with audio** | `fal-ai/veo3.1` | **$0.40 / s** → 5s ≈ **$2.00** |
| B-roll standard without audio | same | **$0.20 / s** |
| B-roll fast 720p/1080p with audio | `fal-ai/veo3.1/fast` | **$0.15 / s** → 5s ≈ **$0.75** |
| 4K with audio | standard | **$0.60 / s** |

Official: [authentication](https://fal.ai/docs/documentation/setting-up/authentication), [Veo 3.1 model page](https://fal.ai/models/fal-ai/veo3.1).

---

## End-to-end spend sketch (one 30s English ad)

Rough order-of-magnitude with defaults (Avatar III twin + short TTS + one 5s Veo B-roll with audio):

| Stage | Backend | Ballpark |
|---|---|---|
| Twin create (once) | HeyGen | ~$2 |
| A-roll 30s Avatar III | HeyGen | ~$0.30 |
| TTS ~500 chars | ElevenLabs | cents on Creator plan / API |
| B-roll 5s + audio | fal Veo 3.1 | ~$2.00 |
| Ingest / ASR / compose / export | local | **$0** |

Retries and Avatar IV/V dominate cost. Prefer `iae run <clip> --dry-run` before any paid call.

---

## Outputs
- Keys in OS keyring or `~/.secrets/<service>-key`
- `iae <backend> key verify` → `ok: true` + account summary
- `iae doctor --keys` → board of present/verified keys

## Failures
| Symptom | Fix |
|---|---|
| `ModuleNotFoundError: httpx` | use `bin/iae`, not system python |
| verify FAIL 401 | `iae <svc> key clear` then `key set` with a fresh key |
| HeyGen 402 / insufficient credits | top up PAYG wallet (not Pro subscription) |
| fal verify 403 | key works; recreate with READONLY/FULL to see balance, or keep API preset for Veo |
| ElevenLabs clone denied | upgrade to Starter+ (IVC) or Creator+ (PVC) |
| Twin billed unexpectedly | API wallet ≠ $49 Pro — see `knowledge/backends/heygen-api-vs-pro.md` |

## Done when
`iae doctor --keys` shows HeyGen (and fal if B-roll) **verify OK**, or you intentionally stop after dry-run with no keys.
