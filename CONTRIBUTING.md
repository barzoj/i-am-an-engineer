# Contributing

## Code
- Python 3.10+, Hatchling, `uv`.
- One CLI group per module under `i_am_an_engineer/` with `register(sub)`.
- Edit skills in `skills/`, then copy to `.agents/skills` and `.claude/skills` (keep them identical).
- Tests must not call real APIs or need real keys.

```bash
uv run --with pytest pytest -q tests
./bin/iae --help
./bin/iae publish check
```

## Knowledge notes
- Use `iae kb new` / `iae kb check`.
- No personal media, no API keys, no real faces or voices.

## Pull requests
- Do not PR recordings, exports, `.env`, or key files.
- Licensed fixture media only under `examples/fixture-readme/`.
- Ask the human before `kb pr` or any public publish.
