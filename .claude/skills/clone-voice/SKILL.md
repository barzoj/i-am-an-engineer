---
name: clone-voice
description: Clone the founder’s English voice (ElevenLabs IVC or HeyGen) and TTS/STS the approved script. Use when A-roll needs a dedicated clone or the twin’s auto voice is not good enough.
---

# Clone voice

## Inputs
- Voice samples in `recordings/voice/` (or motion audio).
- Approved `script/en.md`.
- ElevenLabs and/or HeyGen key.

## Commands
```bash
iae voice clone --samples recordings/voice/* --provider elevenlabs
# or: --provider heygen

iae voice tts --out work/audio/script.mp3
iae voice sts --audio recordings/voice/ref.wav --out work/audio/sts.mp3
```

## Outputs
- `voice.elevenlabs_voice_id` or `heygen.voice_id` in `project.yaml`.
- `work/audio/script.mp3` (TTS).

## Failures
| Symptom | Fix |
|---|---|
| no samples | ingest voice takes; or use twin auto voice and skip |
| no voice_id | run clone first |
| PVC CAPTCHA / slot errors | stay on instant clone for MVP; pause for human if PVC required |

## Done when
TTS file exists or twin `voice_id` is set for generate.
