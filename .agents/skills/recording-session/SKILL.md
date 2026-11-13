---
name: recording-session
description: Guide a 30–60 min English founder shoot for digital-twin source (consent, motion, 2-min monologue, stills, calm voice). Use when the user will record new footage, or asks what to film for HeyGen/ElevenLabs.
---

# Recording session

## Inputs
- Phone or camera, lav if available, plain wall, front light.
- Clothes the ad should live in.

## Commands
```bash
iae record guide
# same content: knowledge/recording/one-session.md
```

## What they must capture
| Block | Output files (after ingest) |
|---|---|
| Consent | kept with vendor; also note in `consent/` |
| Motion 20–40 s expressive (+ calm) | `iae ingest <takes> --kind motion` |
| ~2 min monologue | `--kind motion` |
| Stills close/waist/full | `--kind stills` |
| 15–30 min calm English voice | `--kind voice` |

## Outputs
- Shot list printed.
- After shoot: media ready for **make-founder-ad** ingest step.

## Failures
| Symptom | Fix |
|---|---|
| Only a 10–15 s selfie | also shoot uninterrupted ~2 min monologue |
| Echoey voice samples | re-record calm lav / closer mic |
| They try to nail the final script on camera | stop — twin says the script later |

## Done when
Motion + (ideally) voice takes exist on disk and have been ingested.
