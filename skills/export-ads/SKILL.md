---
name: export-ads
description: Copy composed masters into Meta and LinkedIn export folders and write exports/manifest.json. Use after compose-ad.
---

# Export ads

## Inputs
- `work/compose/ad_*.mp4`
- `export.platforms` in `project.yaml` (default meta, linkedin)

## Commands
```bash
iae export
iae export --platforms meta linkedin
```

## Outputs
- `exports/meta/…`, `exports/linkedin/…`
- `exports/manifest.json`

## Failures
| Symptom | Fix |
|---|---|
| items marked missing | compose missing ratios; fix `reframe.ratios` and re-compose |
| empty exports | run **compose-ad** first |

## Done when
Manifest lists required platform/ratio files without `"missing": true`.
