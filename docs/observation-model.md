# Typed Observation model (V1)

Generic measurements reuse the existing `Observation` class (`Observation → Event → Thing`).
No `MedicalObservation`, `GrowthObservation`, or `MedicalRecord` container.

## Governed predicates

Install via propose → semantic review → apply (see
`semantic_memory.ontology.observation_predicates.OBSERVATION_PREDICATE_PROPOSALS`):

| Predicate | Kind | Cardinality | Domain → Range |
|-----------|------|-------------|----------------|
| `observationOf` | entity | many | Observation → Thing |
| `observationType` | string | one | Observation |
| `numericValue` | number | one | Observation |
| `unit` | string | one | Observation |

V1 keeps **one numeric measurement per Observation entity**. A later reading creates a
new Observation; it does not supersede the previous one. Corrections use
`correct_statement` / supersession on the mistaken statements.

## Temporal fields (existing)

| Field | Meaning |
|-------|---------|
| `statement.observed_at` / predicate `occurredAt` | When the measurement was taken |
| `statement.asserted_at` | When AtlasSynapse accepted the claim |
| `valid_from` / `valid_to` | Claim validity window (orthogonal to lifecycle) |

Do not put import time in `observed_at`.

## Units

Canonical strings (`cm`, `kg`, `C`, `kWh`). No units ontology in V1.

## Agent playbook

### Create one Observation

Prefer `assert_batch` so the entity and required statements commit atomically:

1. Entity `Observation` (deterministic name if helpful: `{subject} — {type} — {YYYY-MM-DD}`).
2. `observationOf` → subject Thing/Person.
3. `observationType` → e.g. `height`.
4. `numericValue` → typed number; set `observed_at` to the measurement time.
5. `unit` → e.g. `cm`.
6. Optional: `ensure_source` + `add_evidence` for screenshots / reports.

### Add a subsequent reading

Create a **new** Observation. Do not correct or supersede the prior reading unless
the prior reading was wrong.

### Correct a reading

Use `correct_statement` on the mistaken `numericValue` (or other) statement. History
is preserved via supersession.

### Retrieve a measurement series

Prefer `query_observations` (HTTP `POST /v1/observations/query`, MCP agent tool)
over N+1 `get_timeline` / `search_statements` calls:

1. Pass `entity_id` of the subject Thing (e.g. person or device).
2. Optionally filter `observation_type` and `observed_from` / `observed_to`.
3. Read typed `value`, `unit`, `observed_at` from the page — do not parse descriptions.
4. `total` counts only complete, non-ambiguous matches; incomplete/ambiguous candidates
   appear in `skipped` / `ambiguous` (never silently dropped).
5. `observed_at` is returned as stored; when `date_precision` is present on the
   numericValue metadata, treat clock time as a placeholder, not measured time.

### Duplicate import vs identical values

- Same MCP `idempotency_key` → replay (safe).
- Same source measurement id in metadata (when available) → treat as the same import.
- Same person + type + date + value alone is **not** proof of sameness; two real
  measurements can match. Do not auto-merge solely on equal numbers.

### Approximate dates

Leave `observed_at` null when unknown; record precision in statement metadata
(`date_precision`) rather than inventing a calendar day.

### Ontology clarification / reviewer failure

- `outcome_reason=needs_clarification` → `answer_semantic_clarification`.
- `outcome_reason=review_failed` → retry the same proposal (`challenge_ontology_review`
  or re-answer the still-open clarification). Do not treat as semantic rejection.
- Re-proposing the same key reuses the open proposal (`open_proposal_reused`).

### Provenance quality

| Kind | Representation |
|------|----------------|
| Screenshot / app export | Source + evidence; metadata `source_type` |
| Parent-reported approximate | Evidence + lower confidence; not a diagnosis |
| Clinician-confirmed | Source reliability / evidence |
| Derived (BMI, percentile) | Separate Observation or Claim with derivation note |
| LLM hypothesis | Prefer Claim path; never promote to medical fact by assertion alone |

## Agent anti-patterns

- Do not dump measurement series into Person.`description` (cardinality one → conflicts).
- Do not store magnitudes only in free-text `description` or opaque statement metadata
  when `numericValue` is available.
- Prefer `observationOf` over generic `relatedTo` for subject-of-observation.
