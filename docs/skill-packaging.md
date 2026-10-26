# Semantic Memory skill — packaging design (Phase 3)

**Status:** design only. Do **not** publish, ZIP-submit, or paste into ChatGPT
as the production distribution path until this document is reviewed and the
live connector mechanism is verified.

**Git source of truth:** `skills/semantic-memory/` (Phase 2).

## Three layers

| Layer | Role | Availability |
| --- | --- | --- |
| **MCP tools** | Live data + governed actions | AtlasSynapse Secure MCP Tunnel → stdio `mcp` |
| **Plugin skill** | Procedural knowledge with progressive disclosure | Agent Plugins `skills/*/SKILL.md` (+ `references/`) |
| **Connector instructions** | Always-on, lightweight guidance | Connector / developer-mode paste field (if used) |

Tools answer *what the system can do now*. The skill answers *how to decide*.
Connector instructions should stay thin if used at all.

## Investigation: can the current AtlasSynapse connector ship a native skill?

### What OpenAI supports

Agent Plugins package:

```text
plugin.json          # portable Agent Plugins manifest
skills/…/SKILL.md    # progressive disclosure (name/description first)
mcp.json             # typically remote streamable-http MCP (+ OAuth)
assets/              # icons
```

Official skill docs describe progressive disclosure: ChatGPT/Codex see
name + description first, then load full `SKILL.md` (and referenced files)
when the skill is selected. That is the preferred UX.

Sibling reference: Palanoria (`/srv/satellite/apps/relatia/plugin/`) ships a
directory plugin with **remote** MCP (`https://mcp…/mcp` + OAuth), not a tunnel.

### What AtlasSynapse runs today

```text
ChatGPT connector (Connection: Tunnel)
  → OpenAI Secure MCP Tunnel
  → satellite tunnel-client
  → docker compose … run --rm -T mcp   (stdio JSON-RPC)
```

There is **no** public HTTPS MCP URL and **no** OAuth MCP app for AtlasSynapse
V1. `tunnel/README.md` is the operational path.

### Conclusion (current stack)

| Option | Progressive disclosure | Fits current tunnel | Recommendation |
| --- | --- | --- | --- |
| **A. Plugin ZIP with `skills/` + keep Tunnel for tools** | Yes (skill package) | Tools stay on Tunnel; plugin may be skills-only / empty `mcpServers` | **Preferred next experiment** — verify ChatGPT accepts skills-only (or skills + separately attached Tunnel connector) without requiring remote MCP in the same ZIP |
| **B. Full plugin like Palanoria** (`mcp.json` remote HTTP + OAuth) | Yes | Requires new remote MCP + auth surface | **Not V1** unless product prioritizes directory publish |
| **C. Generated connector instructions from Git skill** | **No** (flattened) | Works today as interim | **Documented interim only** |

**Do not** treat manually pasted connector instructions as the final
architecture. If A fails in practice, fall back to C with explicit limitations
documented below, while keeping Git as the only edited source.

## Interim mechanism (C) — limitations

If operators paste a generated instruction blob:

- ChatGPT may receive the **entire** procedure at once (no progressive
  disclosure of `references/`).
- Drift risk if anyone edits the paste without regenerating from Git.
- No automatic coupling to plugin version / skill version metadata.

Mitigations:

1. Generate from `skills/semantic-memory/` (script TBD; not shipped until
   reviewed).
2. Header must include `skill_version`, `requires_package_version_min`, and
   “regenerate; do not hand-edit”.
3. Prefer a **short** always-on stub + pointer to install the native skill
   when A is verified.

## Proposed package layout (when A is approved)

```text
plugin/                              # distribution mirror (generated or synced)
  plugin.json
  mcp.json                           # empty mcpServers OR omitted until remote MCP exists
  assets/                            # from assets/brand.yaml / logo_mcp
  skills/
    semantic-memory/                 # copy of repo skills/semantic-memory/
```

Repo-canonical path remains `skills/semantic-memory/` so Cursor and non-plugin
consumers share one tree. A future `scripts/sync_plugin_skills.sh` (or ZIP
builder) must **copy from Git**, never the reverse.

## Version relationship

Skill frontmatter (`metadata.atlas_synapse`) declares:

- `skill_version`
- `requires_package_version_min`
- `expected_tools` (agent catalog)

Agents must compare `expected_tools` to live `tools/list` (see
`skills/semantic-memory/references/tools.md`). Missing tools → documented
fallback or disclose — never silent degradation.

## Evaluation (Phase 4 pointer)

Scenarios live in `skills/semantic-memory/references/evaluation.md`. Run with
and without the skill against the live 18-tool agent surface after packaging
path A or interim C is chosen.

## Explicit non-goals (this design)

- Publishing to the OpenAI plugin directory
- Hand-maintained duplicate instruction docs outside Git
- Domain-specific medical (or other) skills for V1
- Hardcoded ontology catalogs inside the skill
