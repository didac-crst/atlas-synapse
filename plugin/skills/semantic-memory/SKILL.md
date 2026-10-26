---
name: semantic-memory
description: >
  Use AtlasSynapse governed semantic memory — identity-safe writes, ontology
  discovery when uncertain, temporal facts, Claims vs Statements, Observations,
  and retrieval. Prefer live MCP tools over inventing schema or IDs.
metadata:
  atlas_synapse:
    skill_version: "0.2.2"
    requires_package_version_min: "0.1.0.dev6"
    expected_tool_surface: agent
    expected_tools:
      - search_memory
      - get_relevant_context
      - get_timeline
      - query_observations
      - search_ontology
      - get_ontology_context
      - assert_statement
      - assert_batch
      - correct_statement
      - retract_statement
      - repair_supersession_integrity
      - ensure_source
      - ingest_source_content
      - get_source_content
      - search_source_content
      - answer_identity_clarification
      - answer_semantic_clarification
      - challenge_ontology_review
      - propose_class
      - propose_predicate
      - get_ontology_proposal
      - apply_ontology_proposal
---

# AtlasSynapse Semantic Memory

AtlasSynapse is a **general-purpose, governed semantic memory**. You discover
the live ontology through tools; you do **not** rely on a hardcoded catalog of
classes or predicates, and you do not invent entity IDs, statement IDs, or
schema keys.

MCP tools are the source of truth for what this connector session can do.
Before following a workflow that needs a named tool, confirm it appears in the
current tool list. If a documented tool is missing, use an explicitly documented
fallback in `references/tools.md` or disclose the limitation — do **not**
silently improvise (for example, do not parse free-text descriptions as a
substitute for `query_observations`).

`expected_tools` in metadata is **declarative compatibility documentation** for
authors/CI — not an automatic runtime gate. Still compare against live
`tools/list` before relying on a named tool.

Load `references/` only when needed for the current task.

## Operating principles

1. **Server owns identity.** Pass `subject_entity_id` / `object_entity_id` when
   known, otherwise `EntityInput` (`canonical_name` + `class_key`). Never
   invent UUIDs. On `outcome=CLARIFY`, call `answer_identity_clarification`.
2. **Discover on uncertainty, reuse when verified.** Call `search_ontology` /
   `get_ontology_context` when the concept or predicate is unfamiliar, a write
   hits schema/validation failure, the ontology may have changed, or you are
   about to `propose_*`. If this workflow already established valid keys (e.g.
   `Observation` + `numericValue`), reuse them — do not rediscover every time.
3. **Facts vs speech-acts.** Domain **Statements** are world beliefs. **Claims**
   (`epistemicKind` ∈ hypothesis / recommendation / question / assertion) are
   speech-acts; their interiors are not auto-asserted as facts. Retrieval
   excludes Claims unless `include_claims=true`. See `references/epistemology.md`.
4. **Write eligibility is multi-factor.** Authorization, relevance, epistemic
   status, evidence/confidence, and schema readiness are separate decisions.
   Well-typed ≠ true or worth storing. See `references/epistemology.md`.
5. **Evolve knowledge correctly.** Mistaken records → `correct_statement` /
   `retract_statement`. World change over time → temporally scoped new asserts
   (not “correct away” true history). Contradictory sources → preserve
   uncertainty; do not invent a winner. See `references/knowledge-evolution.md`.
6. **Never pass `actor_key`.** The MCP server injects the actor. Mutations need
   `request_id` + `idempotency_key`; prefer `dry_run=true` to preview.
   Prefer `return_mode=standard` on statement mutations.
7. **Propose ≠ apply.** Ontology changes: discover → `propose_*` → review →
   `get_ontology_proposal` → `apply_ontology_proposal` only when ready. Challenge
   with `challenge_ontology_review` / answer semantic clarifications as directed.

## Default tool map

| Intent | Tools |
| --- | --- |
| Look something up | `search_memory`, `get_relevant_context` |
| Entity history | `get_timeline` |
| Typed measurement series | `query_observations` |
| Unfamiliar modeling / before propose | `search_ontology` → `get_ontology_context` |
| Store one fact | `assert_statement` |
| Atomic Observation / multi-fact | `assert_batch` |
| Fix mistaken record / withdraw | `correct_statement`, `retract_statement` |
| Bad supersession edge | `repair_supersession_integrity` |
| Attach/read document text (OCR, articles) | `ingest_source_content`, `get_source_content`, `search_source_content` |
| Identity clarify | `answer_identity_clarification` |
| Ontology lifecycle | `propose_*`, clarifications, `apply_ontology_proposal` |

## Decision rules (short)

- **Do not assert** when exploring, when unauthorized, when evidence is too weak
  for a domain fact, or when class/predicate is unknown — discover or ask first.
- **Do not propose** a new class/predicate until `search_ontology` shows no
  adequate reuse candidate (unless the user explicitly overrides after you
  surface the candidates).
- **Do not** use `correct_statement` for ordinary world-change or to silence
  contradictory sources — see `knowledge-evolution.md`.
- Open `conflict_ids` are not auto-resolved on the agent surface; disclose and
  escalate rather than inventing resolve tools.
- On governance / capability / validation errors: read the error code, fix the
  input or escalate — do not bypass gates or claim success.

## References (progressive disclosure)

| File | Load when |
| --- | --- |
| `references/tools.md` | Tool missing, arg shapes, version/capability checks |
| `references/ontology-discovery.md` | Modeling uncertainty, propose vs reuse |
| `references/identity.md` | CLARIFY, EntityInput, no silent merges |
| `references/epistemology.md` | Write eligibility; facts vs Claims vs Decisions |
| `references/knowledge-evolution.md` | Mistake vs change vs conflicting evidence |
| `references/temporal.md` | `observed_at` / validity vs lifecycle |
| `references/observations.md` | Typed Observation `assert_batch` example / query |
| `references/documents.md` | OCR/article text on existing Document; no PDF binary |
| `references/governance.md` | Provenance limits, dry-run, quality repair |
| `references/evaluation.md` | Skill eval scenarios (authors / reviewers) |
