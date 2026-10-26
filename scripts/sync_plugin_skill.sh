#!/usr/bin/env bash
# Copy canonical skills/semantic-memory into plugin/skills/ (Git → package).
# Never copy the other direction.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$ROOT/skills/semantic-memory"
DST="$ROOT/plugin/skills/semantic-memory"

if [[ ! -f "$SRC/SKILL.md" ]]; then
  echo "missing canonical skill at $SRC/SKILL.md" >&2
  exit 1
fi

mkdir -p "$ROOT/plugin/skills"
rm -rf "$DST"
cp -a "$SRC" "$DST"
echo "synced $SRC -> $DST"
