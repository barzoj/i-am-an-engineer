#!/usr/bin/env bash
# CI / local smoke: install CLI, verify skills layout, dry-run on a synthetic clip.
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

echo "==> skills layout (npx skills add .)"
if command -v npx >/dev/null 2>&1; then
  # Agent Skills installer; accept non-zero if the local registry UX differs — still verify tree.
  npx --yes skills add "$ROOT" || true
fi
test -f skills/make-founder-ad/SKILL.md
test -f .agents/skills/make-founder-ad/SKILL.md
test -f .claude/skills/make-founder-ad/SKILL.md
# entry skill must mention dry-run + make me an ad discovery path
grep -q "make me an ad" skills/make-founder-ad/SKILL.md
grep -q "dry-run" skills/make-founder-ad/SKILL.md

echo "==> synthetic clip + dry-run"
WORKDIR="$(mktemp -d)"
CLIP="$WORKDIR/sample.mp4"
PROJ="$WORKDIR/project"
mkdir -p "$PROJ"
uv run --project "$ROOT" python - <<PY
from pathlib import Path
from i_am_an_engineer.media import make_synthetic_clip
make_synthetic_clip(Path("$CLIP"), seconds=1.0, width=320, height=240)
print("wrote", "$CLIP")
PY
iae run "$CLIP" --dry-run --project "$PROJ" --ratios 9:16 1:1
test -f "$PROJ/work/dry_run.json"
test -f "$PROJ/work/compose/ad_9x16.mp4"
test -f "$PROJ/work/compose/ad_1x1.mp4"
test -f "$PROJ/exports/manifest.json"
iae publish check --project "$PROJ" || true

echo "==> unit tests"
uv run --with pytest pytest -q tests

echo "SMOKE OK"
