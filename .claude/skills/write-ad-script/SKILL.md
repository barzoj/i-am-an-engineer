---
name: write-ad-script
description: Draft or edit a 20–45 s English founder ad script (hook/body/offer) into script/en.md and export teleprompter lines. Use when copy is missing, weak, or the user asks to rewrite the ad.
---

# Write an English ad script

## Inputs
- Product/pain in plain language.
- Existing `project.yaml` / `script/en.md` (from `iae init`).

## Structure (required)
1. Hook — one concrete pain sentence  
2. Body — 2–3 sentences, credible, no unverifiable claims  
3. Offer — one clear next step  

English only. Target 20–45 seconds spoken.

## Commands
```bash
# edit script/en.md then:
iae script teleprompter --out work/teleprompter.txt
```

## Outputs
- `script/en.md` locked with the founder’s approval.
- `work/teleprompter.txt` — plain lines for recording/TTS.

## Failures
| Symptom | Fix |
|---|---|
| teleprompter empty | remove heading-only lines; write full sentences |
| Non-English copy | translate/rewrite to English; `language: en` is enforced |
| Medical/legal overclaim | rewrite to what they can stand behind |

## Done when
Founder approves `script/en.md` and teleprompter export is non-empty.
