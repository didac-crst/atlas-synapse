# Governance, provenance, recovery

## Capabilities and gates

Visibility ≠ authorization. Even listed tools may reject writes without the
right actor capabilities. Ontology apply revalidates at commit; there is no
force path.

Prefer `dry_run=true` to preview mutations. Dry-run does not persist knowledge
writes.

## Provenance on the agent surface (what is actually available)

| Capability | Agent surface (22 tools) | Advanced / HTTP |
| --- | --- | --- |
| Assert / correct / retract facts | Yes | Yes |
| `ensure_source` | Yes | Yes |
| `ingest_source_content` / `get_source_content` / `search_source_content` | Yes | Yes |
| `add_evidence` (statement↔source link) | **No** (typical) | Yes |
| Optional `confidence` on assert/correct | Yes (statement field) | Yes |
| Optional statement `metadata` | Yes where the request schema allows | Yes |
| PDF / binary blob ingest | **No** | **No** (text formats only) |

**What the agent can do today**

- Persist domain Statements / Observation batches.
- Create/reuse Sources and attach **text** document revisions (HTML/Markdown/text),
  including OCR transcriptions on an existing Document via `document_entity_id`.
- Read and search stored document bodies.
- Optionally set `confidence` when the schema allows.

**What the agent still cannot do on the default ChatGPT catalog**

- Attach Evidence rows linking a *statement* to a source/excerpt (`add_evidence`
  advanced). Document *body* storage does not require this.
- Ingest PDF/binary files — use OCR/transcription text instead and say so.

**Honesty rule:** If only a fact was stored (no `ensure_source` /
`ingest_source_content`), say the **fact** was recorded — do not claim a
document body or evidence link was attached. If document text was ingested,
say the **text revision** was stored — do not claim a PDF binary was stored.
If `add_evidence` was not called, do not claim statement-level evidence rows.

Unknown source reliability stays null when provenance APIs are used — null is
not “perfect reliability”.

See also `documents.md`.

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
