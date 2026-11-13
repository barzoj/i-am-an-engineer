# i-am-an-engineer

A public MIT agent toolkit that turns **one recording session of a founder** into **professional English ad videos** performed by **their own digital twin** (face + cloned voice), then cut like a real ad: multiple framings, B-roll, captions, motion graphics.

Works with Claude Code, Codex, Cursor, Gemini CLI, GitHub Copilot, OpenCode, and anything else that reads `AGENTS.md`.

## Start here
1. **If the user drops a video and says “make me an ad” (or similar), load `skills/make-founder-ad/SKILL.md` immediately** and follow its loop end to end. That entry skill routes to the other skills. Do not invent a parallel pipeline.
2. **Search the knowledge base:** `bin/iae kb search "<topic>"` (`knowledge/INDEX.md`).
3. **At the end, share what you learned** with `iae kb new` / `iae kb check` (ask before any PR).

Acceptance bar: a fresh agent that only installed this plugin/skills must complete the flow from a clip + “make me an ad” by following skills only. See `docs/TESTING.md`.

## Tools
- **`bin/iae`** is the Python CLI (`uv` sets it up).
  - PATH: `export PATH="$PWD/bin:$PATH"`, or `uv tool install git+https://github.com/barzoj/i-am-an-engineer`.
  - Every group has `--help`: `init`, `doctor`, `record`, `script`, `ingest`, `transcribe`, `twin`, `voice`, `generate`, `broll`, `compose`, `export`, `run`, `publish`, `kb`, `backend`, plus `heygen` / `elevenlabs` / `fal` / `deepinfra` for `key set|status|clear`.
- **Keys:** `iae <backend> key set` → OS keyring (Linux `secret-tool`) or `~/.secrets`. Env vars win (`HEYGEN_API_KEY`, `ELEVENLABS_API_KEY`, `FAL_KEY`, `DEEPINFRA_API_KEY`).
- **MCP:** fal at `https://mcp.fal.ai/mcp` (needs `FAL_KEY`); optional local `python -m i_am_an_engineer.mcp_server`. Configured in `.mcp.json`, `.cursor/mcp.json`, `.vscode/mcp.json`, `opencode.json`, `gemini-extension.json`.
- **Skills** live in `skills/` and are copied to `.agents/skills` and `.claude/skills` (a test fails while they differ).

## Rules
- English only (scripts, captions, clones).
- Never commit real faces, voices, exports, recordings, or secrets.
- Do not fake HeyGen consent.
- Disclosure is a `project.yaml` setting (`disclosure.enabled`), **off by default** — no moralizing text.
- Ask before spending API credits or opening PRs.

## Working on the toolkit
- Python 3.10+, PyYAML, httpx. Code in `i_am_an_engineer/`, one module per CLI group with `register(sub)`.
- Tests: `uv run --with pytest pytest -q tests`.
- CI runs help for every group, skill-copy equality, mocked API tests, and `iae publish check`.
