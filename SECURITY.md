# Security

## API keys
Store keys with the CLI, not in `project.yaml` or git:

```bash
iae heygen key set
iae elevenlabs key set
iae fal key set
iae deepinfra key set
```

Precedence: environment variable → OS keyring → `~/.secrets/<service>-key` → `.env`.

Env vars: `HEYGEN_API_KEY`, `ELEVENLABS_API_KEY`, `FAL_KEY`, `DEEPINFRA_API_KEY`.

## Media
Never commit founder recordings, A-roll, B-roll, or exports. `.gitignore` covers the usual paths; `iae publish check` blocks them in CI.

## Reporting
Open a private security advisory or email the maintainer listed on the GitHub repo. Do not file public issues that include keys or personal media.
