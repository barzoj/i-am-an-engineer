---
name: setup-backends
description: Configure HeyGen, ElevenLabs, and fal API keys for i-am-an-engineer; run doctor; explain API credits vs HeyGen Pro. Use when keys are missing, doctor fails, or before twin/A-roll/B-roll.
---

# Setup backends

## Inputs
- User ready to paste API keys (or env already set).
- Optional: existing `project.yaml`.

## Commands
```bash
command -v iae || export PATH="$PWD/bin:$PATH"
iae doctor
iae heygen key set          # https://platform.heygen.com
iae elevenlabs key set      # optional
iae fal key set             # https://fal.ai/dashboard/keys
iae backend status
iae heygen key status
iae elevenlabs key status
iae fal key status
```

Env overrides (win over keyring): `HEYGEN_API_KEY`, `ELEVENLABS_API_KEY`, `FAL_KEY`.

## Outputs
- Keys in OS keyring (Linux `secret-tool`) or `~/.secrets/<service>-key`.
- `iae doctor` shows masked keys + ffmpeg presence.

## Failures
| Symptom | Fix |
|---|---|
| `no heygen key` | `iae heygen key set` or export `HEYGEN_API_KEY` |
| ffmpeg MISSING | install ffmpeg; re-run `iae doctor` |
| API 401 after key set | wrong key; `iae <svc> key clear` then `key set` |
| Twin/generate billed unexpectedly | HeyGen **API credits** are separate from $49 Pro — read `knowledge/backends/heygen-api-vs-pro.md` |

## Done when
`iae doctor` exits 0 with ffmpeg present and at least HeyGen (+ fal if B-roll needed) marked set.
