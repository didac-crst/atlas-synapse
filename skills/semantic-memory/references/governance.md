# Governance, provenance, recovery

## Capabilities and gates

Visibility ≠ authorization. Even listed tools may reject writes without the
right actor capabilities. Ontology apply revalidates at commit; there is no
force path.

Prefer `dry_run=true` to preview mutations. Dry-run does not persist knowledge
writes.

## Provenance on the agent surface (what is actually available)

| Capability | Agent surface (18 tools) | Advanced / HTTP |
| --- | --- | --- |
| Assert / correct / retract facts | Yes | Yes |
| `ensure_source` | **No** | Yes |
| `add_evidence` | **No** | Yes |
| `ingest_source_content` / search source content | **No** | Yes |
| Optional `confidence` on assert/correct | Yes (statement field) | Yes |
| Optional statement `metadata` | Yes where the request schema allows | Yes |

**What the agent can do today**

- Persist the domain Statement (or Observation batch) itself.
- Optionally set `confidence` when the schema allows.
- Mention the user's source in the conversational reply.

**What the agent cannot do on the default ChatGPT catalog**

- Create or reuse a first-class Source record.
- Attach Evidence rows linking a statement to a source/excerpt.

**Honesty rule:** If only the fact was stored, say that the **fact** was
recorded — do **not** claim provenance/evidence was attached. When the user
needs durable source linkage, disclose that `ensure_source` / `add_evidence`
require an advanced surface or HTTP path, and offer to record the fact now
without fabricated provenance IDs.

Unknown source reliability stays null when provenance APIs are used — null is
not “perfect reliability”.

## Conflicts (related limit)

Open conflicts may be recorded server-side (`conflict_ids` on writes).
`find_conflicts` is advanced; resolve/dismiss are HTTP-only on the current
MCP registration. See `knowledge-evolution.md`. Do not invent a resolve.

## Quality / supersession repair

If responses surface memory-quality issues about supersession integrity, use
`repair_supersession_integrity` with the given `issue_id` and an explicit
`successor_statement_id`. Do not guess successors.

## Governance error recovery

1. Read stable `error_code` / outcome fields.
2. Fix inputs (unknown class → discover; ambiguity → clarify; open conflict →
   disclose coexistence / escalate — do not fake resolve).
3. Challenge ontology review only with new rationale/evidence via
   `challenge_ontology_review`.
4. Never invent “success” after a rejection.
