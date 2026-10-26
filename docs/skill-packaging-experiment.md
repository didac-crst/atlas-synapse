# Option A — minimal skill install experiment

**Goal:** Verify that ChatGPT can load the `semantic-memory` skill from a
native plugin package **while** continuing to use the existing 18-tool
AtlasSynapse Secure MCP Tunnel connector.

**Non-goals:** Do not restart or reconfigure the tunnel. Do not write
production knowledge unless the evaluator explicitly intends to. Do not submit
the package to the public plugin directory.

## Package

| Artifact | Path |
| --- | --- |
| Canonical skill | `skills/semantic-memory/` (v0.2.1+) |
| Experiment plugin tree | `plugin/` |
| ZIP | `dist/atlas-synapse-skill-plugin.zip` (generated, usually gitignored) |

```bash
./scripts/build_skill_plugin_zip.sh
```

`plugin/mcp.json` has `"mcpServers": {}` on purpose. Tools stay on the tunnel.

## Pass criteria

1. Plugin ZIP installs in ChatGPT (developer / local plugin path).
2. Skill `semantic-memory` appears among available skills (name/description
   discoverable).
3. In a conversation with the AtlasSynapse **tunnel** connector enabled, MCP
   `tools/list` still exposes the 18 agent tools (including
   `search_ontology` / `get_ontology_context`).
4. When a semantic-memory task is posed, ChatGPT can activate the skill
   (progressive disclosure of `SKILL.md` / references) **and** call tunnel MCP
   tools in the same session.
5. Asking “is the semantic-memory skill available?” plus a read-only
   `search_ontology` call succeeds without inventing tools.

## Fail modes to record

| Observation | Implication |
| --- | --- |
| Skills-only ZIP rejected (requires remote MCP in same package) | Option A blocked; document and prefer Option C interim or Option B later |
| Skill installs but never activates alongside tunnel tools | Need connector-instructions bridge or UI wiring |
| Installing plugin disconnects / replaces tunnel tools | Do not proceed; restore tunnel-only setup |
| Skill loads but references/ progressive disclosure broken | Flatten critical rules into `SKILL.md` body temporarily |

## After the experiment

- **Pass:** keep Git as source of truth; automate sync/ZIP only as needed;
  then run the 17 evaluation scenarios with the skill installed.
- **Fail:** keep tunnel; use generated connector instructions (Option C) with
  documented loss of progressive disclosure; do not hand-edit pastes.

Update this doc with the actual ChatGPT UI path used and the pass/fail result
when the experiment is run.
