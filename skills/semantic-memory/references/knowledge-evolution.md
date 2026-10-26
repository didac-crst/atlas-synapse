# Correction vs change vs conflict

These are different knowledge-management situations. Do **not** route all of
them through `correct_statement`.

| Situation | Meaning | Agent workflow (agent surface) |
| --- | --- | --- |
| **Mistaken record** | The stored statement was never an accurate report of the world (wrong value, wrong dates, wrong object). | `correct_statement` on that `statement_id` (supersedes; history kept). Or `retract_statement` if it should not remain as current knowledge. |
| **World changed** | The prior statement was true for an interval; a later state is different. | Prefer a **new** `assert_statement` with non-overlapping `valid_from` / `valid_to`. If the prior open-ended interval should end, `correct_statement` only to set an accurate `valid_to` on the *historical* statement (and/or assert the successor). Do not supersede away a still-true past interval. |
| **Contradictory sources** | Two reports disagree; neither is known to be a recording error. | Preserve both as distinct assertions (or Claims when speech-acts). Do **not** arbitrarily “correct” one into the other. Overlapping cardinality-one writes may record `conflict_ids`; both statements remain asserted. |

## Why this matters

`correct_statement` always **supersedes** the previous statement (lifecycle →
`SUPERSEDED`). That is correct for fixing a mistake. Using it to “update” a
fact that was historically true erases the temporal meaning of that past
interval.

Non-overlapping validity windows do **not** create cardinality conflicts
(implemented behavior). Overlapping cardinality-one statements can both stay
asserted with open conflict metadata.

## Conflicts on the agent surface (contract limit)

- Mutation responses may include `conflict_ids`.
- `find_conflicts` is **advanced** (not in the default 18-tool agent catalog).
- `resolve_conflict` / `dismiss_conflict` are HTTP APIs; they are **not**
  registered as MCP tools on the current server surface.

Therefore ChatGPT on the agent connector **must not** claim it resolved a
conflict. If `conflict_ids` appear: surface the uncertainty to the user, keep
both sides visible via retrieval, and escalate to an advanced/HTTP operator
path when explicit resolve/dismiss is required.

## Choosing among tools

```text
Was the prior statement wrong as a record?
  yes → correct_statement / retract_statement
  no  → Did the world change over time?
          yes → new assert with temporal bounds (+ optional correct valid_to)
          no  → Contradictory evidence?
                  yes → keep coexistence; do not invent a winner
                  no  → ask / dry_run before writing
```
