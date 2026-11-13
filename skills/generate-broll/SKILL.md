---
name: generate-broll
description: Generate short B-roll clips via fal Veo 3.1 from project.yaml shot list or a one-off prompt. Use while or after A-roll to feed the edit.
---

# Generate B-roll

## Inputs
- `FAL_KEY` set.
- `broll.shots` in `project.yaml` and/or a `--prompt`.

## Commands
```bash
iae fal key status
iae broll
iae broll --prompt "soft window light on a clean desk, no people" --duration 5
```

## Outputs
- Clips under `work/broll/` + `shot_*.json` metadata.
- Veo carries SynthID watermark (cannot disable).

## Failures
| Symptom | Fix |
|---|---|
| no fal key | `iae fal key set` |
| no shots | pass `--prompt` or edit `broll.shots` |
| queue timeout | retry; shorten duration; check fal status page |

## Done when
One or more B-roll MP4s exist (optional for dry-run; recommended for final ads).
