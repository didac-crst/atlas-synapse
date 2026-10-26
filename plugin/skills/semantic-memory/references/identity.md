# Identity resolution

## Rules

- AtlasSynapse owns MATCH / CREATE / CLARIFY. Agents do not “resolve then assert”
  with guessed IDs.
- Prefer known `entity_id` when the session already established it.
- Otherwise pass `EntityInput`: `canonical_name` + `class_key` (and aliases /
  external refs when available).
- On `outcome=CLARIFY`, use `answer_identity_clarification` with
  `chosen_entity` / `create_new` / `reject` as appropriate.
- No silent entity merges. Merges are advanced, explicit operations.

## Ambiguity

Treat same-name different people/orgs as distinct until clarified. Do not
assert conflicting facts onto a guessed entity.
