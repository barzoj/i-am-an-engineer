---
name: make-founder-ad
description: Turn one founder video (or a full recording session) into professional English digital-twin ads — Meta/LinkedIn framings, B-roll, captions, loudness. Use when the user says "make me an ad", "make an ad from this video", drops/AirDrops/uploads an iPhone .mov/.mp4, or wants founder ads performed by their own digital twin (face + cloned voice). Default entry skill for this toolkit; runs the whole loop and routes to sub-skills.
---

# Make a founder ad (digital twin)

You are the ad producer. The user gives **a video** (often a raw iPhone `.mov` from AirDrop) and something like **"make me an ad"**. You take it all the way to exportable English ads — preferably performed by **their own digital twin** (HeyGen face + cloned voice), cut like a real commercial.

This is the **default starting skill** for the i-am-an-engineer toolkit. Follow this loop end to end. Route into the companion skills named below for depth; do not invent alternate pipelines.

## Your tools

`iae` is the toolkit CLI (`bin/iae` in the repo). Claude Code’s plugin puts it on PATH; other agents’ installs often do not.

```bash
command -v iae || export PATH="$PWD/bin:$PATH"
# or once: uv tool install git+https://github.com/barzoj/i-am-an-engineer
iae --help
iae doctor
```

| Need | Command |
|---|---|
| Scaffold project | `iae init --name "<Brand>"` |
| Keys (keyring; env wins) | `iae heygen key set`, `iae elevenlabs key set`, `iae fal key set` |
| Recording shot list | `iae record guide` |
| Teleprompter from script | `iae script teleprompter --out work/teleprompter.txt` |
| Ingest local path **or** http(s) URL; normalize iPhone HEVC/HDR/VFR | `iae ingest <path-or-url> --kind motion` |
| No-API smoke (ingest→captions→framings) | `iae run <path-or-url> --dry-run` |
| Twin / consent / looks | `iae twin create\|consent\|looks` |
| Voice clone / TTS | `iae voice clone\|tts\|sts` |
| A-roll / B-roll | `iae generate aroll`, `iae broll` |
| Compose / export / gate | `iae compose`, `iae export`, `iae publish check` |

Companion skills: **setup-backends**, **recording-session**, **write-ad-script**, **train-digital-twin**, **clone-voice**, **generate-aroll**, **generate-broll**, **compose-ad**, **export-ads**, **publish-check**, **share-field-notes**.

## Intake (keep it short)

1. Locate the **input video** (path, AirDrop destination, or share URL). If missing, ask once.
2. Confirm language: **English only**.
3. Agree done: usually Meta 9:16/4:5/1:1 (+ LinkedIn) with captions, ~20–45 s script.
4. Ask whether API keys exist (HeyGen / ElevenLabs / fal). If none yet:
   - Still run **`iae run <video> --dry-run`** immediately so they see framings/captions/loudness from their plate.
   - Then follow **setup-backends** before twin/A-roll/B-roll.
5. Start `ADLOG.md` in the working folder: paths, IDs, failures, next step.

Disclosure (`disclosure.enabled` in `project.yaml`) is **off by default**. Do not lecture. Only burn a label if they turn it on.

## The loop

### 0. Project
```bash
iae init --name "<Founder or brand>"
iae doctor
```
**Output:** `project.yaml`, `recordings/`, `script/en.md`, `consent/`, `work/`, `exports/`.  
**Failure:** `project.yaml already exists` → continue unless they want `--force`.

### 1. Ingest the video (always)
Primary path: raw iPhone `.mov` (HEVC/H.265, often HDR/Dolby Vision, VFR, rotation metadata).

```bash
iae ingest "<path-or-https-url>" --kind motion
# stills / voice later:
# iae ingest <files> --kind stills|voice
```

**Output:** normalized SDR H.264 CFR MP4 under `recordings/motion/` (audio kept; rotation baked). Raw copy under `work/ingest/raw/`. Manifest: `work/ingest/manifest.jsonl`.  
**Failure:** ffmpeg missing → install ffmpeg, re-run `iae doctor`. HTML from Drive/iCloud → ask for a direct file or local AirDrop path.

If they only want a local preview with no APIs:
```bash
iae run "<path-or-url>" --dry-run
```
**Output:** `work/compose/ad_*.mp4`, `exports/manifest.json`, `work/dry_run.json`. Then continue the twin path when keys exist.

Route depth: treat ingest details as part of this skill; recording a *new* session → **recording-session**.

### 2. Script (English)
Route: **write-ad-script**. Draft/lock `script/en.md` (20–45 s). Then:
```bash
iae script teleprompter --out work/teleprompter.txt
```
**Failure:** empty teleprompter → script is only headings; write real sentences.

### 3. Backends
Route: **setup-backends**.
```bash
iae heygen key set          # required for twin + A-roll
iae elevenlabs key set      # optional higher-quality voice
iae fal key set             # B-roll (Veo 3.1)
iae backend status
```
Remember: HeyGen **API credits ≠ $49 Pro plan** (`knowledge/backends/heygen-api-vs-pro.md`).

### 4. Twin + consent
Route: **train-digital-twin**.
```bash
iae twin create --footage recordings/motion/<normalized>.mp4
iae twin consent                 # print URL — human completes on camera
iae twin consent --mark-granted  # after they finish
```
**Never fake consent.** Stop until `consent.granted: true`.

### 5. Voice
Route: **clone-voice**. Twin may already have `heygen.voice_id`. Else:
```bash
iae voice clone --samples recordings/voice/* --provider elevenlabs
iae voice tts --out work/audio/script.mp3
```

### 6. A-roll
Route: **generate-aroll**.
```bash
iae generate aroll --ratios 9:16 4:5 1:1 --engine avatar_v
```
**Failure:** consent false → go back to step 4. API 401/402 → keys/credits (setup-backends).

### 7. B-roll
Route: **generate-broll**.
```bash
iae broll
# or: iae broll --prompt "…" --duration 5
```

### 8. Compose
Route: **compose-ad**. Download completed A-roll into `work/aroll/master.mp4` if the job JSON only has a URL, then:
```bash
iae compose --aroll work/aroll/master.mp4
# or plan only: iae compose --plan-only
```
**Output:** `work/compose/ad_9x16.mp4` (etc.), captions ASS, loudness −14 LUFS.

### 9. Export + gate
Route: **export-ads**, then **publish-check**.
```bash
iae export
iae publish check
```
**Failure:** publish check FAIL → fix consent/disclosure/exports/secrets; do not ship.

### 10. Field note (optional)
Route: **share-field-notes**. Ask before any PR.

## Hard rules
- **English only** — scripts, captions, clones.
- **Own likeness only** — their face/voice from their recording; no stock spokesperson.
- **No secrets in git** — keys via `iae <backend> key set` / env; never `project.yaml`.
- **No personal media in git** — recordings/work/exports are gitignored; `iae publish check` enforces.
- **Consent is real** — open the HeyGen link; wait; then `--mark-granted`.
- **Disclosure** — configure in YAML; do not moralize.
- **Ask before** spending paid API credits or opening PRs.

## When the user only said “make me an ad” + a file
Do this minimum sequence without waiting for a perfect brief:
1. `iae init` (if needed) → `iae doctor`
2. `iae run "<video>" --dry-run` (immediate tangible outputs)
3. Ask for keys / whether to proceed with HeyGen twin
4. Continue steps 2–9 of the loop

## References
- `knowledge/recording/one-session.md`
- `knowledge/backends/heygen-api-vs-pro.md`
- `knowledge/platforms/meta-linkedin-exports.md`
- `docs/TESTING.md` — agent-level acceptance test
