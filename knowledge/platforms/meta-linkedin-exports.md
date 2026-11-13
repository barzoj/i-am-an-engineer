---
title: Meta and LinkedIn export presets
date: 2026-11-13
status: published
agents: []
---

# Meta and LinkedIn export presets

## Summary

MVP exports copy composed masters into `exports/meta` and `exports/linkedin` with ratios Meta cares about (9:16, 4:5, 1:1) and LinkedIn-friendly squares/vertical/landscape. Loudness target defaults to −14 LUFS.

## Gotchas

1. Missing `ad_4x5.mp4` after compose → ensure `reframe.ratios` includes `4:5` before `iae compose`.
2. Disclosure off in `project.yaml` but burn-in present → `iae publish check` fails on inconsistency.
