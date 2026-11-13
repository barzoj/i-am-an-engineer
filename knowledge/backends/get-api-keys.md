---
title: Get API keys (HeyGen / ElevenLabs / fal)
date: 2026-11-13
status: published
agents: []
---

# Get API keys

## Summary

Follow `skills/setup-backends/SKILL.md` → **Get API keys**. Store with `iae <backend> key set`, validate with `iae <backend> key verify` or `iae doctor --keys` (free account endpoints only). HeyGen needs a PAYG API wallet (not Pro). ElevenLabs Creator+ for PVC. fal credits for Veo B-roll (~$0.40/s with audio on Veo 3.1).

## Gotchas

1. HeyGen Pro subscription ≠ API wallet.
2. fal `API` preset keys may 403 on billing verify — still valid for Veo.
3. Never paste keys into chat or commit them; use keyring / `~/.secrets`.
