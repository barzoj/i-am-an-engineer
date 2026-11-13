# Testing

## What “done” means

The **product is the skills**. A fresh agent that only installed this repo as a plugin and is given **a video file + “make me an ad”** must discover **make-founder-ad** and complete the flow by following skills.

## Agent-level acceptance test (manual)

Use a **clean** agent session with no prior chat about this repo.

### Install (pick one)
| Surface | Install |
|---|---|
| Cursor | Clone or Marketplace; reads `AGENTS.md` + `.cursor/mcp.json` + `.agents/skills` |
| Claude Code | `/plugin marketplace add barzoj/i-am-an-engineer` then `/plugin install i-am-an-engineer@i-am-an-engineer` |
| Skills only | `npx skills add https://github.com/barzoj/i-am-an-engineer` (or `npx skills add .`) |
| CLI | `uv tool install git+https://github.com/barzoj/i-am-an-engineer` **or** from a clone: `export PATH="$PWD/bin:$PATH"` — `bin/iae` self-bootstraps `uv` + deps |

Also: **ffmpeg**, and for the spoken sample below: **espeak-ng**.

### Bootstrap check
On a bare clone, the first command must be:

```bash
export PATH="$PWD/bin:$PATH"
iae doctor
```

`bin/iae` installs `uv` if needed and uses `uv run` (never naked system Python). If you see `ModuleNotFoundError: httpx`, you bypassed `bin/iae`.

### Realistic acceptance sample (ffmpeg + espeak-ng)

Do **not** use the tiny silent/sine `make_synthetic_clip` for acceptance — dry-run captions come from **ASR of spoken English**. Build a no-face spoken plate that is actually **~20 seconds** (a short espeak line alone is only ~9s — use the longer script **and** loop/pad to 20.00s).

```bash
# Exactly 20.00s English TTS plate + solid color (no faces). Dry-run only — never twin-train.
sudo apt-get install -y espeak-ng ffmpeg   # once

TEXT='Most founders cannot deliver a calm confident take on camera. They freeze, they rush, or they sound nothing like the product they ship. Record one clean session instead. Train your own digital twin on that footage. Clone the voice. Then cut a professional English ad with multiple framings, captions, B-roll, and loudness for Meta and LinkedIn. One recording session. Many ads. Your face. Your voice.'

# -s 140 slows speech so the script is nearer 20s before any loop
espeak-ng -v en-us -s 140 -w /tmp/iae-tts.wav "$TEXT"

# Video duration fixed at 20s; -stream_loop -1 + -t 20 pads/loops audio if TTS is short
ffmpeg -y -f lavfi -i color=c=0x1a1a2e:s=1280x720:d=20:r=30 \
  -stream_loop -1 -i /tmp/iae-tts.wav -t 20 \
  -c:v libx264 -pix_fmt yuv420p -c:a aac -shortest \
  -movflags +faststart sample.mov

ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 sample.mov
# expect ~20.00

# Or via the helper (same 20s guarantee):
iae doctor
uv run --project . python -c "
from pathlib import Path
from i_am_an_engineer.media import make_spoken_sample
make_spoken_sample(Path('sample.mov'), seconds=20)
"
```

**ASR note:** dry-run captions come from **faster-whisper** of the plate audio. Wording may **differ slightly** from the espeak script (synthetic TTS is imperfect speech) — expect the same gist and keywords, not a character-perfect match to `$TEXT`.

`sample.mov` / `ADLOG.md` / local `project.yaml` are **gitignored**.

### Prompt
Give the agent **only**:
1. Path to `sample.mov` (or any spoken English clip), and  
2. **make me an ad**

### Expected behavior
1. Loads **make-founder-ad**; bootstraps `bin/iae`.
2. Runs `iae run <clip> --dry-run` without requiring keys.
3. Transcript engine is **faster-whisper** (not stub); `captions.ass` reflects spoken audio (not template `script/en.md` alone). Captions may differ slightly from the synthetic TTS script — see ASR note above.
4. `iae backend status` exits **0** and lists heygen / elevenlabs / fal even when keys are missing.
5. Does **not** twin-train on synthetic samples; stops twin path until real footage + keys + consent.
6. `iae publish check` does not warn about gitignored `sample.mov`.

### Expected artifacts (dry-run / no keys)
- `project.yaml`, `recordings/motion/*.mp4` (normalized H.264 CFR)
- `work/transcripts/*.json` with `"engine": "faster-whisper"` and real `text` / `segments`
- `work/compose/captions.ass` sourced from that transcript
- `work/compose/ad_*.mp4`, `exports/manifest.json`, `work/dry_run.json`

### Synthetic vs real
| Sample | OK for |
|---|---|
| ffmpeg + espeak spoken plate / `make_spoken_sample` | dry-run acceptance only |
| Tiny `make_synthetic_clip` (sine, no speech) | unit tests for normalize — **not** dry-run ASR |
| Real founder iPhone `.mov` | dry-run **and** twin training (after consent) |

## Automated tests

```bash
uv run --with pytest pytest -q tests
./scripts/smoke.sh
```

`scripts/smoke.sh`: `uv tool install .`, `npx skills add .`, spoken sample + `iae run --dry-run`, help checks, unit tests.
