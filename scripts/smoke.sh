#!/usr/bin/env bash
# CI / local smoke: install CLI, verify skills layout, dry-run on a spoken sample.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "==> ensuring uv"
if ! command -v uv >/dev/null 2>&1; then
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi

echo "==> uv tool install ."
uv tool install --force "$ROOT"
export PATH="$HOME/.local/bin:$PATH"
command -v iae
iae --version

echo "==> CLI help"
iae --help >/dev/null
for g in init doctor record script ingest transcribe twin voice generate broll compose export run publish kb backend heygen elevenlabs fal deepinfra; do
  iae "$g" --help >/dev/null
done

echo "==> backend status (must exit 0 with no keys)"
iae backend status >/tmp/iae-backend-status.json
python3 -c "import json; d=json.load(open('/tmp/iae-backend-status.json')); assert d.get('ok') is True; assert 'heygen' in d['keys']"

echo "==> skills layout (npx skills add .)"
if command -v npx >/dev/null 2>&1; then
  npx --yes skills add "$ROOT" || true
fi
test -f skills/make-founder-ad/SKILL.md
test -f .agents/skills/make-founder-ad/SKILL.md
test -f .claude/skills/make-founder-ad/SKILL.md
grep -q "make me an ad" skills/make-founder-ad/SKILL.md
grep -q "dry-run" skills/make-founder-ad/SKILL.md
grep -q "Bootstrap" skills/make-founder-ad/SKILL.md

echo "==> spoken sample + dry-run (faster-whisper captions)"
if ! command -v espeak-ng >/dev/null 2>&1 && ! command -v espeak >/dev/null 2>&1; then
  echo "installing espeak-ng for spoken sample"
  sudo apt-get update -qq
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq --no-install-recommends espeak-ng
fi
WORKDIR="$(mktemp -d)"
CLIP="$WORKDIR/sample.mov"
PROJ="$WORKDIR/project"
mkdir -p "$PROJ"
uv run --project "$ROOT" python - <<PY
from pathlib import Path
from i_am_an_engineer.media import make_spoken_sample
make_spoken_sample(Path("$CLIP"))
print("wrote", "$CLIP")
PY
iae run "$CLIP" --dry-run --project "$PROJ" --ratios 9:16 1:1
test -f "$PROJ/work/dry_run.json"
test -f "$PROJ/work/compose/ad_9x16.mp4"
test -f "$PROJ/work/compose/ad_1x1.mp4"
test -f "$PROJ/exports/manifest.json"
# Captions must come from real ASR, not stub/template
python3 - <<PY
import json
from pathlib import Path
tr = json.loads(Path("$PROJ/work/transcripts").glob("*.json").__iter__().__next__().read_text())
assert tr.get("engine") == "faster-whisper", tr.get("engine")
assert tr.get("text") and not str(tr["text"]).startswith("[stub"), tr.get("text")
ass = Path("$PROJ/work/compose/captions.ass").read_text()
# at least one spoken keyword should appear in ASS
assert any(w in ass.lower() for w in ("founder", "camera", "twin", "english", "ad")), ass[:500]
plan = json.loads(Path("$PROJ/work/compose/plan.json").read_text())
assert str(plan.get("caption_source","")).startswith("transcript:"), plan.get("caption_source")
print("caption ASR OK")
PY
iae publish check --project "$PROJ" || true

echo "==> unit tests"
uv run --with pytest pytest -q tests

echo "SMOKE OK"
