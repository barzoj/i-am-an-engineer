---
name: train-digital-twin
description: Create a HeyGen digital twin from ingested motion footage, drive the consent URL, optionally request looks. Use after ingest when building A-roll from the founder’s likeness.
---

# Train digital twin (HeyGen)

## Inputs
- Normalized motion MP4 in `recordings/motion/` (from `iae ingest`).
- `HEYGEN_API_KEY` configured (`iae heygen key status`).
- `consent.granted` still false until human finishes the link.

## Commands
```bash
iae twin create --footage recordings/motion/<file>.mp4
# writes heygen.avatar_group_id / look_ids / voice_id into project.yaml

iae twin consent
# → open consent_url in a browser; founder records the on-camera statement

iae twin consent --mark-granted
# only after they actually finished

iae twin looks --prompt "navy blazer, soft studio light"
```

## Outputs
- Updated `project.yaml` heygen fields.
- Consent URL JSON on stdout.
- Ready for **generate-aroll** when granted.

## Failures
| Symptom | Fix |
|---|---|
| no key | **setup-backends** |
| footage not found | re-ingest; use normalized `.mp4` path |
| generate blocked / publish check | consent not granted — finish URL then `--mark-granted` |
| resource_limit / payment errors | buy HeyGen **API** credits (not Pro web plan) |

## Done when
`heygen.avatar_group_id` set and `consent.granted: true`.
