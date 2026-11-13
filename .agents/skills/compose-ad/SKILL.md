---
name: compose-ad
description: Local ffmpeg compose — reframe to 9:16/4:5/1:1/16:9, burn English captions (from transcript or script), loudness −14 LUFS, optional disclosure. Use when A-roll (or dry-run plate) is on disk.
---

# Compose ad

## Inputs
- A-roll MP4 (`work/aroll/master.mp4` or normalized plate).
- Captions source:
  - **Preferred after dry-run / ingest:** `work/transcripts/<stem>.json` from `iae transcribe` (faster-whisper of the plate audio).
  - Else: teleprompter lines from `script/en.md`.
- ffmpeg on PATH.

## Commands
```bash
iae compose --plan-only
iae compose --aroll work/aroll/master.mp4 --captions-from work/transcripts/sample.json
iae compose --aroll work/aroll/master.mp4   # falls back to script/en.md
# dry-run already wires transcript captions:
iae run <video> --dry-run
```

## Outputs
- `work/compose/plan.json` (includes `caption_source`)
- `work/compose/captions.ass`
- `work/compose/ad_*.mp4` per `reframe.ratios`

## Failures
| Symptom | Fix |
|---|---|
| ffmpeg not found | install ffmpeg |
| captions from stub/template unexpectedly | pass `--captions-from` or use dry-run (faster-whisper) |
| disclosure mismatch | align `disclosure.*` and re-compose |

## Done when
Per-ratio MP4s exist; for dry-run, `caption_source` starts with `transcript:`.
