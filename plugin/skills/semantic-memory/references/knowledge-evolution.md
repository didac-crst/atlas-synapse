# Correction vs change vs conflict

These are different knowledge-management situations. Do **not** route all of
them through `correct_statement`.

| Situation | Meaning | Agent workflow (agent surface) |
| --- | --- | --- |
| **Mistaken record** | The stored statement was never an accurate report of the world (wrong value, wrong dates, wrong object). | `correct_statement` on that `statement_id` (supersedes; history kept). Or `retract_statement` if it should not remain as current knowledge. |
| **World changed** | The prior statement was true for an interval; a later state is different. | Prefer a **new** `assert_statement` with non-overlapping `valid_from` / `valid_to`. If the prior open-ended interval should end, `correct_statement` may set an accurate `valid_to` — knowing this **supersedes** the prior row (see below). Do not use correction to erase a still-true past interval’s meaning. |
| **Contradictory sources** | Two reports disagree; neither is known to be a recording error. | Preserve both as distinct assertions (or Claims when speech-acts). Do **not** arbitrarily “correct” one into the other. Overlapping cardinality-one writes may record `conflict_ids`; both statements remain asserted. |

## Why this matters

`correct_statement` always **supersedes** the previous statement (lifecycle →
`SUPERSEDED`) and creates a new asserted successor. That preserves an auditable
history, but **only the successor is active** — the prior statement is no longer
an active effective fact, even when you only intended to close `valid_to`.

Implications for agents:

- Closing an open-ended interval via `correct_statement` is still a supersession,
  not an in-place edit. The corrected validity lives on the **new** statement.
- After such a write, verify with `get_timeline` (or relevant retrieval) rather
  than assuming every earlier statement remains active.
- Prefer a fresh temporally bounded `assert_statement` for the new world state
  when that better matches “was true then, different now,” and use correction
  for `valid_to` only when you intentionally replace the open-ended record.

Using `correct_statement` to overwrite object/value as if the past never held
is wrong when the prior interval was genuinely true.

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
