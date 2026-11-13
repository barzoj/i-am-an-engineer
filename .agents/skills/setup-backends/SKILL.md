---
name: setup-backends
description: Configure HeyGen, ElevenLabs, and fal API keys for i-am-an-engineer; run doctor and backend status; explain API credits vs HeyGen Pro. Use when keys are missing, doctor fails, or before twin/A-roll/B-roll.
---

# Setup backends

## Inputs
- User ready to paste API keys (or env already set).
- CLI bootstrapped (`export PATH="$PWD/bin:$PATH"` — `bin/iae` uses uv).

## Commands
```bash
iae doctor
iae backend status          # always exit 0; lists every backend + which keys are missing
iae heygen key set          # https://platform.heygen.com
iae elevenlabs key set      # optional
iae fal key set             # https://fal.ai/dashboard/keys
iae heygen key status
iae elevenlabs key status
iae fal key status
iae backend status          # confirm configured: true where keys exist
```

Env overrides (win over keyring): `HEYGEN_API_KEY`, `ELEVENLABS_API_KEY`, `FAL_KEY`.

## Outputs
- Keys in OS keyring or `~/.secrets/<service>-key`.
- `iae backend status` JSON with `backends[]` and `keys{}` — missing keys are `present: false`, not a crash.

## Failures
| Symptom | Fix |
|---|---|
| `ModuleNotFoundError: httpx` | use `bin/iae`, not system python |
| `no heygen key` on twin/generate | `iae heygen key set` or export `HEYGEN_API_KEY` |
| ffmpeg MISSING | install ffmpeg; re-run `iae doctor` |
| API 401 after key set | `iae <svc> key clear` then `key set` |
| Twin billed unexpectedly | HeyGen **API credits ≠ $49 Pro** — `knowledge/backends/heygen-api-vs-pro.md` |

## Done when
`iae doctor` shows ffmpeg; `iae backend status` lists all backends; at least HeyGen (+ fal if B-roll) `present: true` for the full twin path. No keys is OK for dry-run only.
