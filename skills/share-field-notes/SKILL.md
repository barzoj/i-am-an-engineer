---
name: share-field-notes
description: Search and write knowledge-base notes about digital-twin ad workflows. Use before reinventing a HeyGen/fal quirk, and after a session to leave gotchas for the next agent.
---

# Share field notes

## Inputs
- Something learned (API quirk, recording tip, export gotcha).
- Human OK before any public PR.

## Commands
```bash
iae kb search "heygen"
iae kb new --title "Avatar V consent timing" --kind backends
iae kb check --index
iae kb index
```

## Outputs
- Note under `knowledge/<kind>/`.
- Updated `knowledge/INDEX.md` / `index.json`.

## Failures
| Symptom | Fix |
|---|---|
| missing ## Summary/Gotchas | fill template sections |
| secret-looking assignment | remove keys; never paste credentials |
| human said no to PR | stop after local note |

## Done when
Note passes `iae kb check` and INDEX is current.
