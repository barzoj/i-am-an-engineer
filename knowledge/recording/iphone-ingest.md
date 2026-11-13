---
title: iPhone AirDrop ingest (HEVC / HDR / VFR / rotation)
date: 2026-11-13
status: published
agents: []
---

# iPhone AirDrop ingest

## Summary

The primary founder path is AirDropping or uploading a raw iPhone `.mov` (HEVC/H.265, often HDR/Dolby Vision 10-bit, variable frame rate, rotation metadata). `iae ingest <path-or-url> --kind motion` downloads if needed, then normalizes to SDR H.264 constant frame rate with rotation baked in and audio kept. `iae run <input> --dry-run` runs ingest → faster-whisper transcript → captions from that audio → compose → export with no API keys. Synthetic/no-face samples are dry-run only.

## Gotchas

1. Share links that return HTML (private Drive/iCloud) → ask for a local file or a public direct link.
2. Older ffmpeg without `zscale` → HDR tonemap falls back to `format=yuv420p` only; install a fuller ffmpeg build for better HDR.
3. Portrait clips looking sideways after a dumb copy → always normalize (default); do not pass `--no-normalize` for phone footage.
4. Dry-run captions come from ASR of the plate audio, not `script/en.md` — silent/sine clips fail dry-run; use spoken English (`docs/TESTING.md` espeak recipe).
5. Bare clone: always use `bin/iae` (self-bootstraps uv); system Python alone misses httpx/faster-whisper.
