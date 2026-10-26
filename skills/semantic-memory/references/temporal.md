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
- Correct wrong times with `correct_statement` (immutable history via
  supersession).
- For “how did this evolve?”, prefer `get_timeline` over ad-hoc searches.
