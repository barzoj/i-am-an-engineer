---
name: generate-aroll
description: Render multi-framing HeyGen Avatar V/IV (or cinematic) A-roll from the approved English script and twin. Use after consent is granted.
---

# Generate A-roll

## Inputs
- `consent.granted: true`
- `heygen` look/avatar id in `project.yaml`
- Locked English script

## Commands
```bash
iae generate aroll --ratios 9:16 4:5 1:1 --engine avatar_v
iae generate aroll --engine avatar_iv
iae generate cinematic --ratio 9:16
```

## Outputs
- Job JSON in `work/aroll/<video_id>.json` (`video_id`, `status`, `download_url`).
- Download completed MP4(s) to `work/aroll/master.mp4` (and per-ratio files) before compose.

## Failures
| Symptom | Fix |
|---|---|
| `consent.granted is false` | **train-digital-twin** consent steps |
| no avatar/look id | `iae twin create` |
| pending forever | poll HeyGen dashboard / `GET /v3/videos/{id}`; check webhooks |
| credits exhausted | top up API wallet |

## Done when
At least one completed A-roll MP4 is on disk for compose.
