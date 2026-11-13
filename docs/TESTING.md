# Testing

## What “done” means for this toolkit

The **product is the skills**, not the CLI alone. A fresh agent that only installed this repo as a plugin and is given **a video file + “make me an ad”** must discover **make-founder-ad** and complete the flow by following skills.

## Agent-level acceptance test (manual)

Use a **clean** agent session with no prior chat about this repo.

### Install (pick one)
| Surface | Install |
|---|---|
| Cursor | Clone or Marketplace; agent reads `AGENTS.md` + `.cursor/mcp.json` + `.agents/skills` |
| Claude Code | `/plugin marketplace add barzoj/i-am-an-engineer` then `/plugin install i-am-an-engineer@i-am-an-engineer` |
| Skills only | `npx skills add https://github.com/barzoj/i-am-an-engineer` (or `npx skills add .` from a clone) |
| CLI | `uv tool install git+https://github.com/barzoj/i-am-an-engineer` |

Also ensure `ffmpeg` is on PATH (`iae doctor`).

### Prompt
Give the agent **only**:
1. A sample clip path (synthetic is fine — see below), and  
2. The sentence: **make me an ad**

Do not name skills or spell out the pipeline.

### Expected behavior
1. Discovers / loads **make-founder-ad** (or clearly follows its loop).
2. Runs `iae doctor` / init as needed.
3. Ingests the clip (normalize if `.mov`/HEVC-like) or `iae run <clip> --dry-run`.
4. Produces compose framings + captions + loudness without requiring the human to invent ffmpeg flags.
5. If keys are missing: still finishes the **dry-run** path, then follows **setup-backends** before twin/A-roll.
6. Never commits recordings/secrets; runs `iae publish check` before claiming ship-ready.

### Expected artifacts (dry-run / no keys)
- `project.yaml`
- `recordings/motion/*.mp4` (normalized H.264 CFR)
- `work/transcripts/*.json`
- `work/compose/ad_*.mp4` (ratios from project)
- `work/compose/captions.ass`
- `exports/manifest.json`
- `work/dry_run.json`

### Expected artifacts (full path with keys)
- Twin IDs + `consent.granted: true`
- `work/aroll/*.json` (+ downloaded masters)
- `work/broll/*`
- Platform folders under `exports/meta`, `exports/linkedin`
- `iae publish check` → PASS

## Synthetic sample clip (no faces)

CI and local smoke generate a tiny solid-color MP4 with ffmpeg (no real people):

```bash
python -c "from pathlib import Path; from i_am_an_engineer.media import make_synthetic_clip; make_synthetic_clip(Path('/tmp/iae-sample.mp4'))"
iae run /tmp/iae-sample.mp4 --dry-run --project /tmp/iae-dry --ratios 9:16 1:1
```

## Automated tests

```bash
uv run --with pytest pytest -q tests
./scripts/smoke.sh
```

`scripts/smoke.sh` (also run in GitHub Actions):
1. `uv tool install .` (or project install)
2. `npx skills add .` when network/npm available (non-fatal soft check of `skills/` layout if npx missing)
3. Generate synthetic clip
4. `iae run <clip> --dry-run` and assert compose outputs exist
5. `iae --help` + each group `--help`
6. `iae publish check`

## Unit tests (no real APIs)
- `project.yaml` schema + pipeline plan
- teleprompter export
- media URL rewrite + normalize filter graph
- HeyGen / ElevenLabs / fal clients with **httpx mock transport** (no keys, no network)
- publish-check fail cases
- skill copy equality (`.agents/skills` and `.claude/skills` match `skills/`)
