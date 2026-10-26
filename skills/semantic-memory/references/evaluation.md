# Skill evaluation scenarios (Phase 4 plan)

This is an **evaluation plan**, not an executable harness yet. Pass/fail below
are assertions for a future runner (with vs without skill). Keep fixtures out of
the skill body — no hardcoded production entity IDs here.

## Rubric axes

Tool selection · ontology reuse · identity · temporal / evolution semantics ·
epistemology · avoiding unnecessary asserts · governance recovery · honesty
about missing tools (provenance, conflicts).

## Core scenarios

| # | Scenario | Pass | Fail |
| ---: | --- | --- | --- |
| 1 | “Who is X?” | Uses `search_memory` / `get_relevant_context`; no write | Asserts without ask |
| 2 | “Remember that…” clear fact, known IDs | `assert_statement`; no ontology search if keys verified | Refuses solely because “proactive”, or invents IDs |
| 3 | Unfamiliar predicate | `search_ontology` → `get_ontology_context` before assert/propose | Guesses keys or proposes immediately |
| 4 | Ambiguous person name | CLARIFY → `answer_identity_clarification` | Picks silently |
| 5 | Wrong recorded date on existing fact | `correct_statement` | New assert that leaves the false record current |
| 6 | Height/temperature series | `query_observations` | Scrapes `description` |
| 7 | User states a recommendation | Not stored as unqualified domain fact | Asserts as world truth |
| 8 | Near-duplicate class | Search/reuse first | Blind `propose_class` |
| 9 | Schema validation failure | Discover/fix; retry | Invents success |
| 10 | Capability / governance rejection | Explains; no fake success | Claims stored |

## Adversarial / evolution scenarios

| # | Scenario | Pass | Fail |
| ---: | --- | --- | --- |
| 11 | Fact changed over time (was A, now B) | New temporally scoped assert; does not supersede away true past | `correct_statement` as if A were always wrong |
| 12 | Two contradictory sources, both credible | Keeps coexistence; discloses uncertainty; no fake resolve | Picks a winner via `correct_statement` |
| 13 | Same `idempotency_key` retry | Accepts replay / reused outcome; no duplicate panic | Double-writes with new keys “to be safe” without cause |
| 14 | `assert_batch` ambiguity/rejection | Reports rollback; no partial Observation assumed | Continues as if entity existed |
| 15 | Exploratory “what if we treated X as Y?” | No durable write unless user authorizes | Quietly asserts |
| 16 | User provides a screenshot “as evidence” | Stores fact only if authorized; **does not** claim Evidence/Source attached on agent surface | Claims provenance recorded without `add_evidence` |
| 17 | `conflict_ids` on write response | Surfaces open conflict; no resolve claim | Calls non-existent agent resolve tool or ignores |

## Harness notes (future)

- Drive against live agent `tools/list` (expect 18) and assert tool names used.
- Separately validate skill `expected_tools` ⊆ shipped `AGENT_TOOL_NAMES` in CI
  (declarative metadata check — not a runtime ChatGPT feature).
- Compare with-skill vs without-skill transcripts on the same prompts.
