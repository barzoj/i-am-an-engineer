# i-am-an-engineer

Skills, an `iae` CLI, MCP configs, and a shared knowledge base that let any AI coding agent turn **one recording session of a founder** into **professional English ad videos** performed by **their own digital twin** (face + cloned voice), then cut like a real ad: multiple framings, B-roll, captions, motion graphics.

MIT licensed. English only.

## Install

Pick your agent. Each gets the same skills (Agent Skills format), MCP configs, and the `iae` CLI.

| Agent | Install |
|---|---|
| **Claude Code** | `/plugin marketplace add barzoj/i-am-an-engineer` then `/plugin install i-am-an-engineer@i-am-an-engineer` |
| **Codex** | `codex plugin marketplace add barzoj/i-am-an-engineer` then `codex plugin add i-am-an-engineer@i-am-an-engineer` |
| **Gemini CLI** | `gemini extensions install https://github.com/barzoj/i-am-an-engineer` |
| **VS Code / Copilot** | Enable `chat.plugins.enabled`, run **Chat: Install Plugin From Source**, enter this repo URL |
| **Cursor** | Cursor Marketplace, or clone (reads `AGENTS.md` and `.cursor/mcp.json`) |
| **OpenCode** | Clone and run `opencode` inside it (`opencode.json`), or `opencode plugin add 'github:barzoj/i-am-an-engineer#main::path:plugins/opencode'` |
| **Skills only** | `npx skills add https://github.com/barzoj/i-am-an-engineer` |
| **Anything else** | `git clone https://github.com/barzoj/i-am-an-engineer` and start your agent inside it |

**The `iae` CLI** (install once for agents that do not put `bin/` on PATH):

```bash
uv tool install git+https://github.com/barzoj/i-am-an-engineer
# or from a clone: export PATH="$PWD/bin:$PATH"
iae --help
```

**API keys** (keyring first; env vars win):

```bash
iae heygen key set
iae elevenlabs key set
iae fal key set
# HEYGEN_API_KEY / ELEVENLABS_API_KEY / FAL_KEY still override
```

You also need Git, Python 3.10+, and ffmpeg (`iae doctor`).

> **HeyGen:** API credits at [platform.heygen.com](https://platform.heygen.com) are **separate** from the $49 Pro web plan. See `knowledge/backends/heygen-api-vs-pro.md`.

## One-session → ad workflow

**Agents:** load the **make-founder-ad** skill when the user drops a video and says “make me an ad”. Follow that skill’s loop; it routes to the others. See `docs/TESTING.md`.

1. `iae init --name "Founder Ad"`
2. Ingest a raw iPhone clip (local path or http(s) URL) — normalizes HEVC/HDR/VFR/rotation to SDR H.264 CFR:  
   `iae ingest ./IMG_1234.MOV --kind motion`  
   No keys yet? `iae run ./IMG_1234.MOV --dry-run` still does ingest → captions → framings → export.
3. Or follow `iae record guide` for a full 30–60 min English shoot, then ingest motion/stills/voice.
4. Lock English copy in `script/en.md` → `iae script teleprompter`
5. `iae twin create` → complete consent URL → `iae twin consent --mark-granted`
6. Optional `iae voice clone` / `iae voice tts`
7. `iae generate aroll --ratios 9:16 4:5 1:1`
8. `iae broll` (fal Veo 3.1)
9. `iae compose --aroll <master.mp4>` → `iae export`
10. `iae publish check`

Disclosure is a `project.yaml` setting (`disclosure.enabled`), off by default.

## What's inside

**Skills** (`skills/`, Agent Skills format): make-founder-ad, write-ad-script, recording-session, train-digital-twin, clone-voice, generate-aroll, generate-broll, compose-ad, export-ads, publish-check, share-field-notes, setup-backends.

**CLI groups:** every command has `--help` with examples — `init`, `doctor`, `record`, `script`, `ingest`, `transcribe`, `twin`, `voice`, `generate`, `broll`, `compose`, `export`, `run`, `publish`, `kb`, `backend`, plus per-backend `key` commands.

**Backends:** HeyGen (twin + A-roll), ElevenLabs (voice), fal (Veo 3.1 B-roll), local compose (ffmpeg). Local-GPU twin is a stub with a clear interface.

## Safety
- Never commit real faces, voices, exports, or secrets (`.gitignore` + `iae publish check`).
- Do not fake vendor consent.
- Tests mock HTTP; CI never calls paid APIs.

## License
MIT. See `LICENSE`.
