# Skill evaluation scenarios (Phase 4)

Use these to compare behavior **with** vs **without** the skill. Rubric axes:
tool selection, ontology reuse, identity, temporal correctness, epistemology,
avoiding unnecessary asserts, governance recovery.

| # | Scenario | Expect |
| ---: | --- | --- |
| 1 | “Who is X?” with known person | `search_memory` / `get_relevant_context`; no write |
| 2 | Store a clear fact with known IDs | `assert_statement`; no ontology search if keys already verified |
| 3 | Store fact with unfamiliar predicate | `search_ontology` → `get_ontology_context` before assert/propose |
| 4 | Ambiguous person name | assert → `CLARIFY` → `answer_identity_clarification` |
| 5 | Wrong `valid_from` on existing fact | `correct_statement`; preserve history |
| 6 | Height series for an entity | `query_observations`; no description scraping |
| 7 | User states a recommendation | Claim-shaped handling / no false domain fact (per epistemology) |
| 8 | Propose near-duplicate class | search first; prefer reuse; propose only if needed |
| 9 | Schema validation failure on assert | discover / fix keys; retry; no invent |
| 10 | Governance / capability rejection | explain limitation; no fake success; challenge only when appropriate |

Authors: keep fixtures in the evaluation harness (not in this skill body) so
the skill stays free of hardcoded production entity IDs.
