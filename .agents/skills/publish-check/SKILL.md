---
name: publish-check
description: Gate shipping — consent/disclosure consistency, required exports, block personal media and API keys from git. Use before sharing or opening a PR.
---

# Publish check

## Inputs
- Project with `project.yaml`
- Optional compose plan / exports manifest
- Repo tree for secret/media scan

## Commands
```bash
iae publish check
iae publish check --repo .
```

## Outputs
- stdout: `PASS` / `WARN` / `FAIL` with reasons.
- Exit code 1 on FAIL.

## Failures (must fix)
| FAIL | Fix |
|---|---|
| generate ran but consent.granted false | finish consent |
| disclosure inconsistent with compose plan | align YAML + re-compose |
| missing export ratio | compose + export |
| secret/env or media tracked | remove from git; keep gitignore |

Does **not** lecture about the law — enforces the file.

## Done when
`iae publish check` exits 0.
