#!/usr/bin/env bash
# Build a minimal Agent Plugins ZIP for the Option A skill-install experiment.
# Does not publish, submit for review, or touch the tunnel deployment.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PLUGIN="$ROOT/plugin"
OUT="${1:-$ROOT/dist/atlas-synapse-skill-plugin.zip}"

"$ROOT/scripts/sync_plugin_skill.sh"

python3 - <<'PY' "$PLUGIN"
import json, sys
from pathlib import Path

plugin = Path(sys.argv[1])
errors: list[str] = []

def load(name: str) -> dict:
    path = plugin / name
    if not path.is_file():
        errors.append(f"missing {name}")
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f"{name}: {exc}")
        return {}

manifest = load("plugin.json")
mcp = load("mcp.json")

if manifest:
    if manifest.get("$schema") != "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json":
        errors.append("plugin.json: unexpected $schema")
    for key in ("name", "version", "description"):
        if not manifest.get(key):
            errors.append(f"plugin.json: missing {key}")
    openai = (manifest.get("extensions") or {}).get("com.openai") or {}
    iface = openai.get("interface") or {}
    for key in (
        "displayName",
        "shortDescription",
        "longDescription",
        "developerName",
        "category",
        "composerIcon",
        "logo",
        "privacyPolicyURL",
        "termsOfServiceURL",
        "supportURL",
        "websiteURL",
    ):
        if not iface.get(key):
            errors.append(f"plugin.json interface missing {key}")
    for rel in (
        iface.get("composerIcon"),
        iface.get("composerIconDark"),
        iface.get("logo"),
        iface.get("logoDark"),
        openai.get("onboardingSkill"),
    ):
        if not rel:
            continue
        path = plugin / rel.removeprefix("./")
        if not path.is_file():
            errors.append(f"missing referenced path {rel}")
    skill = plugin / "skills" / "semantic-memory" / "SKILL.md"
    if not skill.is_file():
        errors.append("missing skills/semantic-memory/SKILL.md")

if mcp:
    if mcp.get("$schema") != "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json":
        errors.append("mcp.json: unexpected $schema")
    if "mcpServers" not in mcp:
        errors.append("mcp.json: missing mcpServers")
    # Empty mcpServers is intentional for Option A (tunnel supplies tools).

if errors:
    print("validation failed:", file=sys.stderr)
    for err in errors:
        print(f"  - {err}", file=sys.stderr)
    sys.exit(1)
print("plugin package OK")
PY

mkdir -p "$(dirname "$OUT")"
rm -f "$OUT"
# Archive root = plugin contents (no nesting folder)
(
  cd "$PLUGIN"
  zip -r "$OUT" plugin.json mcp.json README.md assets skills \
    -x "*.DS_Store" -x "**/.git/**"
)
echo "wrote $OUT"
unzip -l "$OUT" | head -40
