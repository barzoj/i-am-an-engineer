# i-am-an-engineer

A public MIT agent toolkit that turns **one recording session of a founder** into **professional English ad videos** performed by **their own digital twin** (face + cloned voice), then cut like a real ad: multiple framings, B-roll, captions, motion graphics.

Works with Claude Code, Codex, Cursor, Gemini CLI, GitHub Copilot, OpenCode, and anything else that reads `AGENTS.md`.

## Start here (do this first)

### 0. Bootstrap the CLI (required on a bare clone)
A fresh clone has **no venv**. `bin/iae` **self-bootstraps**: it installs `uv` if missing, then `uv run` creates `.venv` and installs deps (`httpx`, `faster-whisper`, …). Do **not** call system `python -m i_am_an_engineer` directly.

```bash
export PATH="$PWD/bin:$PATH"
iae doctor          # first call may install uv + sync deps
# or once anywhere: uv tool install git+https://github.com/barzoj/i-am-an-engineer
```

Also need **ffmpeg** on PATH (compose / ingest normalize). For the realistic acceptance sample: **espeak-ng**.

### 1. Entry skill
**If the user drops a video and says “make me an ad” (or similar), load `skills/make-founder-ad/SKILL.md` immediately** and follow its loop end to end. That entry skill routes to the other skills. Do not invent a parallel pipeline.

For **non-interactive / cloud agents**: skip “ask the user” intake steps; run the skill’s **minimum sequence** (init → `iae run <video> --dry-run` → setup-backends only if keys exist for twin path).

### 2. Knowledge base (when to search)
Run `iae kb search "<topic>"` **when stuck, before spending API credits, or when docs conflict** — not as a blocker before dry-run. `knowledge/INDEX.md` has recording / HeyGen API-vs-Pro / export notes.

### 3. Field notes
At the end, share what you learned with `iae kb new` / `iae kb check` (ask before any PR).

Acceptance bar: a fresh agent that only installed this plugin/skills must complete the flow from a clip + “make me an ad” by following skills only. See `docs/TESTING.md`.

## Tools
- **`bin/iae`** — self-bootstrapping Python CLI (always via `uv`).
  - Every group has `--help`: `init`, `doctor`, `record`, `script`, `ingest`, `transcribe`, `twin`, `voice`, `generate`, `broll`, `compose`, `export`, `run`, `publish`, `kb`, `backend`, plus `heygen` / `elevenlabs` / `fal` / `deepinfra` for `key set|status|clear`.
  - **`iae run <input> --dry-run`**: ingest+normalize → **faster-whisper** transcript → captions from that audio → framings / loudness → export. **No API keys.**
  - **`iae backend status`**: lists all backends + keys; **exit 0 even when keys are missing**.
- **Keys:** follow `skills/setup-backends` (get-api-keys). `iae <backend> key set` → keyring/`~/.secrets`. `iae <backend> key verify` and `iae doctor --keys` use free account endpoints only. Env vars win.
- **MCP:** fal at `https://mcp.fal.ai/mcp` (needs `FAL_KEY`); optional `python -m i_am_an_engineer.mcp_server`.
- **Skills** live in `skills/` and are copied to `.agents/skills` and `.claude/skills` (a test fails while they differ).

## Rules
- English only (scripts, captions, clones).
- Never commit real faces, voices, exports, recordings, secrets, `ADLOG.md`, or local `project.yaml` scaffolding (see `.gitignore`).
- Do not fake HeyGen consent.
- Disclosure is a `project.yaml` setting (`disclosure.enabled`), **off by default** — no moralizing text.
- **Synthetic / no-face samples are dry-run only.** Do not call `iae twin create` on them.
- Ask before spending API credits or opening PRs (interactive sessions).

## Working on the toolkit
- Python 3.10+, PyYAML, httpx, faster-whisper. Code in `i_am_an_engineer/`, one module per CLI group with `register(sub)`.
- Tests: `uv run --with pytest pytest -q tests`.
- CI runs help for every group, skill-copy equality, mocked API tests, smoke (`uv tool install`, `npx skills add`, spoken-sample dry-run).
