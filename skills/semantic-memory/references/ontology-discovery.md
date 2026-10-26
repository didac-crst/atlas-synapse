# Ontology discovery (uncertainty-triggered)

## When to discover

Use `search_ontology` then, when a class key is known, `get_ontology_context`:

- The concept or predicate is unfamiliar in this workflow.
- The appropriate predicate / value kind is uncertain.
- An assertion fails with schema / domain / range / cardinality / unknown
  class or predicate errors.
- You suspect the live ontology changed since last verified context.
- You are considering `propose_class` or `propose_predicate`.

## When **not** to discover

- This turn (or an immediately prior successful step) already verified the
  class/predicate keys you will reuse (example: typed Observation writes after
  confirming `Observation` + `observationOf` / `observationType` /
  `numericValue` / `unit`).
- The user supplies explicit, previously applied keys and you have no reason
  to doubt them.
- You are only reading memory with already-resolved entity IDs.

Avoid mechanical “search before every assert” — it adds latency without value.

## Reuse before propose

1. `search_ontology` with the meaning, not a guessed key spelling alone.
2. Inspect promising classes with `get_ontology_context`.
3. Prefer existing predicates that match domain/range/value kind.
4. Propose only when no adequate candidate exists (or the user insists after
   you show reuse options).

Do **not** hardcode a catalog of live classes/predicates in prompts. Bootstrap
examples in product docs are starting points, not a frozen world model.
`get_class` / `get_predicate` are advanced-surface tools — prefer the agent
discovery pair above.
