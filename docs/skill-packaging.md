# Semantic Memory skill — packaging design (Phase 3)

**Status:** design only. Do **not** publish, ZIP-submit, or paste into ChatGPT
as the production distribution path until this document is reviewed and the
live connector mechanism is verified.

**Git source of truth:** `skills/semantic-memory/` (skill_version 0.2.0+).

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
V1. `tunnel/README.md` is the operational path. **Leave this tunnel deployment
unchanged** while experimenting with skill packaging.

### Conclusion (current stack)

| Option | Progressive disclosure | Fits current tunnel | Release criterion |
| --- | --- | --- | --- |
| **A. Minimal plugin with skill + existing tunnel for tools** | Yes (skill package) | Tools stay on Tunnel; plugin may be skills-only / empty `mcpServers` | **Gate:** prove ChatGPT can install a minimal skill package **and** still use the separately connected tunnel. Do **not** build the full packaging pipeline until this experiment passes. |
| **B. Full remote MCP plugin** (`mcp.json` HTTP + OAuth) | Yes | Requires new remote MCP + auth surface | Longer-term; not required for V1 |
| **C. Generated connector instructions from Git skill** | **No** (flattened) | Works today as interim | Acceptable fallback only after A is attempted; document loss of progressive disclosure |

**Do not** treat manually pasted connector instructions as the final
architecture. Prefer verifying A with a **minimal** experimental package
(stub skill or current skill tree) before investing in ZIP builders, sync
scripts, or directory submission.

## Release sequence (revised)

1. Keep tunnel MCP / 18-tool agent surface as-is (no packaging-driven redeploy).
2. Manually assemble a minimal Agent Plugins package pointing at
   `skills/semantic-memory/` (or a tiny probe skill) and test install in ChatGPT
   alongside the existing Tunnel connector.
3. Only if A works: add sync/ZIP automation that **copies from Git → plugin/**.
4. If A fails: document failure mode; use C as interim with regenerate-from-Git
   discipline.

## Interim mechanism (C) — limitations

If operators paste a generated instruction blob:

- ChatGPT may receive the **entire** procedure at once (no progressive
  disclosure of `references/`).
- Drift risk if anyone edits the paste without regenerating from Git.
- No automatic coupling to plugin version / skill version metadata.

Mitigations:

1. Generate from `skills/semantic-memory/` (script TBD; not shipped until A is
   tested or explicitly abandoned).
2. Header must include `skill_version`, `requires_package_version_min`, and
   “regenerate; do not hand-edit”.
3. Prefer a **short** always-on stub + pointer to install the native skill
   when A is verified.

## Proposed package layout (only after A is proven)

```text
plugin/                              # distribution mirror (generated or synced)
  plugin.json
  mcp.json                           # empty mcpServers OR omitted until remote MCP exists
  assets/                            # from assets/brand.yaml / logo_mcp
  skills/
    semantic-memory/                 # copy of repo skills/semantic-memory/
```

Repo-canonical path remains `skills/semantic-memory/` so Cursor and non-plugin
consumers share one tree. Any future sync script must **copy from Git**, never
the reverse.

## Version / `expected_tools` metadata

Skill frontmatter (`metadata.atlas_synapse`) declares:

- `skill_version`
- `requires_package_version_min`
- `expected_tools` (agent catalog)

Treat `expected_tools` as **declarative compatibility metadata**:

- Agents: compare needed tools to live `tools/list` (session truth).
- CI / packaging tests (when added): assert `expected_tools` ⊆ shipped
  `AGENT_TOOL_NAMES` and document surface mismatches.

It is not an automatic ChatGPT runtime compatibility API.

## Evaluation (Phase 4 pointer)

Scenarios and pass/fail assertions:
`skills/semantic-memory/references/evaluation.md`.
Run with and without the skill against the live 18-tool agent surface after
packaging path A or interim C is chosen.

## Explicit non-goals (this design)

- Publishing to the OpenAI plugin directory before A is proven
- Building full packaging automation before the minimal A experiment
- Hand-maintained duplicate instruction docs outside Git
- Domain-specific medical (or other) skills for V1
- Hardcoded ontology catalogs inside the skill
- Changing the tunnel deployment as part of skill packaging experiments
