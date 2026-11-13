---
name: make-founder-ad
description: Turn one founder video (or a full recording session) into professional English digital-twin ads — Meta/LinkedIn framings, B-roll, captions, loudness. Use when the user says "make me an ad", "make an ad from this video", drops/AirDrops/uploads an iPhone .mov/.mp4, or wants founder ads performed by their own digital twin (face + cloned voice). Default entry skill for this toolkit; runs the whole loop and routes to sub-skills.
---

# Make a founder ad (digital twin)

You are the ad producer. The user gives **a video** (often a raw iPhone `.mov` from AirDrop) and something like **"make me an ad"**. You take it all the way to exportable English ads — preferably performed by **their own digital twin** (HeyGen face + cloned voice), cut like a real commercial.

This is the **default starting skill**. Follow this loop. Route into companion skills for depth; do not invent alternate pipelines.

## 0. Bootstrap (always first on a bare clone)

```bash
export PATH="$PWD/bin:$PATH"
iae doctor
```

`bin/iae` **installs `uv` if needed** and runs through `uv run` so `httpx` / `faster-whisper` resolve. Never use system Python alone. Need **ffmpeg**. For building the acceptance spoken sample: **espeak-ng**.

## Your tools

| Need | Command |
|---|---|
| Doctor / keys board | `iae doctor`, `iae backend status` (exit 0 even with no keys) |
| Scaffold | `iae init --name "<Brand>"` |
| Keys | `iae heygen\|elevenlabs\|fal key set` |
| No-API path | `iae run "<video>" --dry-run` |
| Ingest URL/path | `iae ingest "<path-or-url>" --kind motion` |
| Twin / voice / A-roll / B-roll | see companion skills |
| Compose / export / gate | `iae compose`, `iae export`, `iae publish check` |

Companion skills: **setup-backends**, **recording-session**, **write-ad-script**, **train-digital-twin**, **clone-voice**, **generate-aroll**, **generate-broll**, **compose-ad**, **export-ads**, **publish-check**, **share-field-notes**.

## When the user only said “make me an ad” + a file

**This is the default for cloud / non-interactive agents** (do not block on clarifying questions):

1. Bootstrap: `export PATH="$PWD/bin:$PATH"` → `iae doctor`
2. `iae init --name "Founder Ad"` if no `project.yaml`
3. Start `ADLOG.md` (gitignored)
4. **`iae run "<video>" --dry-run`** immediately  
   - Ingest+normalize → **faster-whisper** transcript of the **actual audio** → captions from that transcript → framings / −14 LUFS → export  
   - Works with **no API keys**
5. `iae backend status` then `iae publish check`
6. If keys are available, continue twin path (steps below). If not, stop after dry-run and say twin/A-roll/B-roll need **setup-backends**.

Interactive sessions may still confirm language / done criteria / keys — but never instead of step 4.

## The full loop (with keys)

### Project
```bash
iae init --name "<Founder or brand>"
iae doctor
iae backend status
```

### Ingest
Primary path: raw iPhone `.mov` (HEVC/HDR/VFR/rotation).

```bash
iae ingest "<path-or-https-url>" --kind motion
# or the dry-run which includes ingest:
iae run "<path-or-url>" --dry-run
```

**Captions:** dry-run burns captions from **ASR of the plate audio**, not from the template `script/en.md`. After dry-run, replace/lock `script/en.md` via **write-ad-script** for the twin TTS path.

**Synthetic / no-face samples** (ffmpeg + espeak): **dry-run only**. Never `iae twin create` on them. See `docs/TESTING.md`.

### Script → Backends → Twin → Voice → A-roll → B-roll → Compose → Export → Gate
Follow the companion skills in order. Consent must be real. `iae publish check` before claiming ship-ready.

## Hard rules
- English only.
- Own likeness only for twin training (real founder footage + consent).
- No secrets / personal media / `ADLOG.md` / local project scaffolding in git.
- Disclosure off by default; no moralizing.
- Ask before paid API spend or PRs (interactive).

## KB search
Search (`iae kb search`) when stuck or before API spend — not required before dry-run.

## References
- `docs/TESTING.md` — acceptance test + spoken sample recipe (ffmpeg + espeak-ng)
- `knowledge/recording/iphone-ingest.md`
- `knowledge/backends/heygen-api-vs-pro.md`
