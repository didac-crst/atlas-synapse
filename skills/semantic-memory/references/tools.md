# Tools, versions, and missing-capability behavior

## Skill ↔ runtime relationship

| Field | Meaning |
| --- | --- |
| `metadata.atlas_synapse.skill_version` | This skill document revision |
| `requires_package_version_min` | Minimum AtlasSynapse package the workflows assume |
| `expected_tool_surface` | Prefer `agent` (ChatGPT default) |
| `expected_tools` | Declarative list of tools the workflows teach |

`expected_tools` is **compatibility metadata** for documentation and CI (e.g.
assert ⊆ `AGENT_TOOL_NAMES`). It is **not** an automatic runtime check inside
ChatGPT. In a live session, compare needed tools to the exposed `tools/list`.

Package version may appear in server instructions / deploy notes. Advanced
diagnostics (`get_runtime_config`) are **not** on the agent surface — do not
assume that tool exists in ChatGPT.

## Arg shapes

| Pattern | Tools | Notes |
| --- | --- | --- |
| Flat args | `search_ontology`, `get_ontology_context`, `get_timeline`, `get_ontology_proposal` | Top-level properties (`query`, `class_key`, …) |
| `{ "payload": { … } }` | Most mutations and composite reads (`search_memory`, `assert_*`, `query_observations`, …) | Do not invent `actor_key` |

## If a documented tool is missing

| Missing tool | Allowed behavior |
| --- | --- |
| `query_observations` | Disclose limitation. Do **not** reconstruct series by scraping `description` text. Offer `get_relevant_context` / `get_timeline` only as a weaker, explicitly labeled substitute. |
| `search_ontology` / `get_ontology_context` | Do not invent class/predicate keys. Ask the user for keys they already know, or stop before proposing. |
| `assert_batch` | Fall back to sequenced `assert_statement` only when the user accepts non-atomic risk; say so. |
| `correct_statement` | Do not invent supersession manually; disclose and stop. |
| `answer_identity_clarification` | Do not pick an ambiguous entity; ask the user and wait for a path that can resume CLARIFY. |
| `ensure_source` / `add_evidence` | Expected absent on agent surface. Store the fact only if authorized; **do not** claim provenance was attached. |
| `find_conflicts` / resolve tools | Expected absent on agent surface. Disclose open `conflict_ids`; do not invent resolve. |
| Any write tool | Prefer read-only help; never invent success. |

When several expected tools are absent, treat the connector as a **partial
surface** and state which workflows are unavailable.
