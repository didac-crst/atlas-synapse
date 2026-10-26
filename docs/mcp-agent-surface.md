# MCP agent surface (`feat/mcp-agent-surface`)

## Principle

**Expose tools by agent intent, not by internal service capability.**

Tool visibility is **UX / context optimization**, not security. Capability checks,
review gates, idempotency, and audit still apply to every mutation.

## Surfaces

| Surface | Purpose | ChatGPT default |
| --- | --- | --- |
| `agent` | Normal reasoning + memory | **Yes** (`MCP_TOOL_SURFACE=agent`) |
| `advanced` | Investigation / low-level | Usually no |
| `admin` | Ops / governance extras | No |
| `all` | Full registry | Dev / Cursor |

Configured via `MCP_TOOL_SURFACE`. One MCP server; `tools/list` and dispatch are
filtered. Advanced/admin tools remain available when the surface is raised —
HTTP APIs are unchanged.

## Counts (this branch)

| Catalog | Tool count |
| --- | ---: |
| Full registry (`all`) | **43** (incl. aliases) |
| Default `agent` | **22** |

Roughly a **~50% reduction** in tools presented to ChatGPT vs the full registry.

## Agent catalog

```text
search_memory
get_relevant_context
get_timeline
query_observations

search_ontology
get_ontology_context

assert_statement
assert_batch
correct_statement
retract_statement
repair_supersession_integrity

ensure_source
ingest_source_content
get_source_content
search_source_content

answer_identity_clarification
answer_semantic_clarification
challenge_ontology_review

propose_class
propose_predicate
get_ontology_proposal
apply_ontology_proposal
```

(`get_proposal` remains on the advanced surface as an alias.
`get_class` / `get_predicate` stay advanced. `add_evidence` stays advanced —
document *body* storage uses `ingest_source_content`, not evidence rows.)

### Why these are agent-shaped

| Tool | Intent |
| --- | --- |
| `search_memory` | “Look something up” |
| `get_relevant_context` | “What do we know about X?” |
| `get_timeline` | “How did this evolve?” |
| `query_observations` | “List typed measurements for an entity” |
| `search_ontology` | “Which classes/predicates match this meaning?” |
| `get_ontology_context` | “What predicates apply to this class?” |
| `assert_statement` | “Store this fact” |
| `assert_batch` | “Atomically store related facts / Observations” |
| `correct_statement` | “Fix this fact” |
| `retract_statement` | “Withdraw this fact” |
| `repair_supersession_integrity` | “Fix this bad supersession edge” |
| `ensure_source` | “Create/reuse a provenance source” |
| `ingest_source_content` | “Attach article/OCR text to a Document/source” |
| `get_source_content` | “Read stored document text / revision” |
| `search_source_content` | “Find a passage inside a document body” |
| `answer_identity_clarification` | “Which Didac?” |
| `answer_semantic_clarification` | “Answer ontology clarification” |
| `challenge_ontology_review` | “Retry / challenge after review_failed or rejection” |
| `propose_*` / `apply_*` | Ontology change lifecycle |

Document content supports `content_format` ∈ `{html, markdown, text}` only.
PDF/binary blobs are **not** a supported ingest format — store OCR/transcription
text (preserving original language) against an existing Document via
`document_entity_id` instead of inventing a parallel document store.

Ontology discovery is for **semantic uncertainty** (unfamiliar concept, unsure
predicate, validation failure, possible ontology drift, before proposing). Do
not rediscover known, verified concepts on every assertion.

Ontology `apply_ontology_proposal` with `dry_run=true` returns `outcome=WOULD_APPLY`,
`projected=true`, and statement-style `operation_mode` / `would_persist` fields — the
embedded proposal snapshot is a projection, not committed state.

## Hidden from agent (and why)

| Tool | Why not default |
| --- | --- |
| `supersede_statement` | Storage semantics; use `correct_statement` |
| `get_entity_neighborhood` | Folded into `get_relevant_context` |
| `search_entities` / `search_statements` | Prefer `search_memory` |
| `search_semantic_memory` | Advanced alias of `search_memory` |
| `get_class` / `get_predicate` | Prefer `search_ontology` + `get_ontology_context` |
| `create_entity` / `get_entity` | Covered by assert EntityInput + context |
| `get_statement` / `explain_statement` | Prefer mutation `return_mode=standard` |
| `add_evidence` | Statement↔source evidence links; body text uses ingest |
| `merge_entity` | Explicit advanced ops |
| `get_runtime_config` | Diagnostics |
| `propose_constraint` / alias / parent | Less common ontology ops |
| `report_feedback` | Ops signal |

## Scenario coverage (agent-only)

```text
"Who is Didac?"                          → search_memory / get_relevant_context
"Airbus role context"                    → get_relevant_context / get_timeline
"Siena height series"                    → query_observations
"How do I model a measurement?"          → search_ontology → get_ontology_context
"Correct the start date"                 → correct_statement
"Store this new fact"                    → assert_statement (discover only if unsure)
"Import many Observations atomically"    → assert_batch
"Attach OCR/transcription to Document"   → ingest_source_content (+ get_source_content)
"Search inside document body"            → search_source_content
"This Didac might already exist"         → assert → answer_identity_clarification
"Propose a new ontology concept"         → search_ontology first → propose_*
"Reviewer failed / challenge decision"   → challenge_ontology_review
"Apply the approved proposal"            → get_ontology_proposal → apply_ontology_proposal
```

See also [observation-model.md](observation-model.md) for typed measurement patterns.

## Deploy note

Tunnel/MCP compose should set `MCP_TOOL_SURFACE=agent` (default). Cursor/dev
can use `advanced` or `all`.
