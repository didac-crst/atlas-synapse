# AtlasSynapse plugin package (Option A experiment)

**Status:** controlled install experiment only. Not a public directory submission.

This folder packages the **Semantic Memory skill** for ChatGPT Agent Plugins.
Live MCP tools continue to come from the existing **Secure MCP Tunnel**
connector — `mcp.json` intentionally has an empty `mcpServers` object.

## Source of truth

| Path | Role |
| --- | --- |
| `../skills/semantic-memory/` | Canonical skill (edit here) |
| `skills/semantic-memory/` | Copy synced into this package |
| `../tunnel/` | Production MCP path (do not change for this experiment) |

Refresh the embedded skill before building a ZIP:

```bash
./scripts/sync_plugin_skill.sh
./scripts/build_skill_plugin_zip.sh
# → dist/atlas-synapse-skill-plugin.zip
```

## Install test (ChatGPT)

1. Keep the production AtlasSynapse **Tunnel** connector connected (18 tools).
2. Import/install this plugin ZIP via ChatGPT’s plugin developer / local plugin
   flow (product UI varies; do not submit for public review).
3. Confirm both are available in the same conversation:
   - MCP tools from the tunnel (`search_ontology`, `assert_statement`, …)
   - Skill `semantic-memory` discoverable / loadable when relevant
4. Ask: whether the semantic-memory skill is installed, then run a read-only
   ontology search — without writing production knowledge unless intended.

If ChatGPT cannot combine a skills-only ZIP with a separate tunnel connector,
record the failure in `docs/skill-packaging-experiment.md` and fall back to
interim connector instructions (Option C).
