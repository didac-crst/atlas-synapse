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

## Agent anti-patterns

- Do not dump measurement series into Person.`description` (cardinality one → conflicts).
- Do not store magnitudes only in free-text `description` or opaque statement metadata
  when `numericValue` is available.
- Prefer `observationOf` over generic `relatedTo` for subject-of-observation.
