# Temporal semantics

| Field | Meaning |
| --- | --- |
| `asserted_at` | When AtlasSynapse accepted the statement |
| `observed_at` | When the source observed / measured it |
| `valid_from` / `valid_to` | When the proposition was true in the world |

Lifecycle (active / superseded / retracted) is **orthogonal** to validity.
There is no `expired` status.

## Agent habits

- Put measurement time in `observed_at`, not import time.
- For “how did this evolve?”, prefer `get_timeline`.
- Fix **wrong** recorded times or values with `correct_statement` (supersession).
- For **genuine change over time**, assert a new temporally scoped statement;
  see `knowledge-evolution.md`. Closing a prior open interval uses
  `correct_statement` only to set an accurate `valid_to` — not to erase the past.

## Intervals and conflicts

Non-overlapping `valid_from`/`valid_to` windows for the same
subject+predicate typically coexist without conflict. Overlapping
cardinality-one statements may both remain asserted with conflict metadata.
Do not treat overlap as automatic permission to supersede one side.
