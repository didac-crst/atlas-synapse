# Typed Observations

Generic measurements reuse the live `Observation` class and governed
predicates. Confirm keys via discovery when this workflow has not verified them
yet; then reuse for subsequent readings.

## Create (atomic `assert_batch`)

Link new Observation entities to statements with `client_item_id` /
`subject_client_item_id` (or `object_client_item_id`). Exactly one subject ref
and exactly one typed object field per statement item. MCP wraps the body in
`payload`; do **not** send `actor_key` (server injects it).

Domain-neutral example (shape matches the implemented batch contract /
`test_assert_batch_creates_observation_atomically`). Replace UUIDs and times
with session values; prefer `dry_run=true` first.

```json
{
  "payload": {
    "request_id": "<uuid>",
    "idempotency_key": "<unique-string>",
    "dry_run": false,
    "entities": [
      {
        "client_item_id": "obs-1",
        "canonical_name": "Lab Sensor A temperature 2026-03-01",
        "class_key": "Observation",
        "namespace_key": "core"
      }
    ],
    "statements": [
      {
        "client_item_id": "of-1",
        "subject_client_item_id": "obs-1",
        "predicate_key": "observationOf",
        "object_entity_id": "<known-subject-entity-uuid>"
      },
      {
        "client_item_id": "type-1",
        "subject_client_item_id": "obs-1",
        "predicate_key": "observationType",
        "object_string": "temperature"
      },
      {
        "client_item_id": "val-1",
        "subject_client_item_id": "obs-1",
        "predicate_key": "numericValue",
        "object_number": 21.5,
        "observed_at": "2026-03-01T12:00:00Z"
      },
      {
        "client_item_id": "unit-1",
        "subject_client_item_id": "obs-1",
        "predicate_key": "unit",
        "object_string": "C"
      }
    ]
  }
}
```

### Expected success shape

- `status`: `succeeded` (enum `BatchStatus.SUCCEEDED`)
- New Observation appears under `created` (entity item `obs-1`)
- Linked statements appear under `created` (or `reused` on idempotent retry)
- `ambiguous`, `rejected`, and `ontology_required` are empty
- On ambiguity / rejection / ontology-required: the batch **rolls back entirely**
  (no partial Observation left behind)

### Identity notes

- Prefer a known `object_entity_id` for `observationOf` when the subject was
  already resolved in-session.
- If the subject is unresolved, use `object: { "canonical_name", "class_key" }`
  instead of inventing a UUID; handle `ambiguous` / CLARIFY paths — do not guess.
- Later readings = **new** Observation entities (new `client_item_id`s), not
  supersession of the prior reading.

## Correct a bad reading

`correct_statement` on the mistaken statement (usually `numericValue`), not on
an earlier true reading that simply differs from a newer measurement.

## Retrieve series

`query_observations` with subject `entity_id` (optional type / time filters).

If `query_observations` is unavailable, disclose the gap — do not scrape
descriptions as a silent substitute.
