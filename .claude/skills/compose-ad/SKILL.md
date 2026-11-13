---
name: compose-ad
description: Local ffmpeg compose — reframe to 9:16/4:5/1:1/16:9, burn English captions, loudness −14 LUFS, optional disclosure. Use when A-roll (or dry-run plate) is on disk.
---

# Compose ad

## Inputs
- A-roll MP4 path (`work/aroll/master.mp4` or normalized plate from dry-run).
- `script/en.md` for captions.
- ffmpeg on PATH.

## Commands
```bash
iae compose --plan-only
iae compose --aroll work/aroll/master.mp4
# dry-run already does this via: iae run <video> --dry-run
```

## Outputs
- `work/compose/plan.json`
- `work/compose/captions.ass`
- `work/compose/ad_9x16.mp4`, `ad_4x5.mp4`, `ad_1x1.mp4`, `ad_16x9.mp4` (per `reframe.ratios`)

## Failures
| Symptom | Fix |
|---|---|
| ffmpeg not found | install ffmpeg |
| needs --aroll | pass master path or use dry-run |
| disclosure mismatch | align `disclosure.enabled` / burn_in with plan; see publish-check |

## Done when
Per-ratio MP4s exist under `work/compose/`.
