"""i-am-an-engineer: one recording session → professional English digital-twin ads.

Subcommands (see `iae --help`):
  init       scaffold project.yaml and folders
  doctor     check Python, ffmpeg, keys, backends
  record     print the recording-session shot list
  script     export teleprompter lines from the approved English script
  ingest     hash, inspect, and store takes into the project
  transcribe transcribe ingested audio/video takes
  twin       create / consent / looks for the HeyGen digital twin
  voice      clone and TTS/STS via ElevenLabs or HeyGen
  generate   render A-roll (Avatar V/IV) or cinematic
  broll      generate B-roll clips (fal Veo 3.1 first)
  compose    cut A-roll + B-roll, captions, loudness, framings
  export     write platform presets (Meta, LinkedIn) + manifest
  run        enabled pipeline stages
  publish    consistency / safety checks before sharing
  kb         knowledge base search / new / check / index
  backend    list configured backends
  heygen     HeyGen API helpers and `key set|status|verify|clear`
  elevenlabs ElevenLabs helpers and `key set|status|verify|clear`
  fal        fal helpers and `key set|status|verify|clear`
  deepinfra  DeepInfra key helpers (optional later backend)
"""

__version__ = "0.1.0"
__doc_short__ = (
    "Agent toolkit that turns one founder recording session into professional "
    "English ad videos performed by their own digital twin."
)
