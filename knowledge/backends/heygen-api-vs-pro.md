---
title: HeyGen API credits vs Pro plan
date: 2026-11-13
status: published
agents: []
---

# HeyGen API credits vs the $49 Pro plan

## Summary

HeyGen API credits are a **standalone** PAYG USD wallet at [platform.heygen.com](https://platform.heygen.com). A Creator/Pro/Business web subscription does **not** fund the API. Automating `iae twin` / `iae generate` needs an API key ([docs](https://developers.heygen.com/docs/api-key)) and wallet top-up ([pricing help](https://help.heygen.com/en/articles/10060327-heygen-api-pricing-explained)). No free API credits since Feb 2026; PAYG credits expire after 12 months. Verify with `iae heygen key verify` (`GET /v3/users/me`).

## Gotchas

1. Paying for Pro and wondering why the CLI 401s / 402s → create an API key and buy API credits separately.
2. Avatar III digital twin A-roll ~$0.60/min; Avatar IV twin ~$4.83/min; Avatar V ~$7.20/min (confirm live table).
3. Free API credits ended Feb 2026 → budget PAYG before rendering Avatar V retries.
