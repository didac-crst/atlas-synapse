# Facts, Claims, Decisions, and write eligibility

## Domain Statements (facts)

Subject–predicate–object beliefs about the world. These are what ordinary
retrieval returns. Schema validity alone does **not** make a statement true or
worth storing.

## Claims (speech-acts)

`Claim` entities carry `epistemicKind`:

- `hypothesis`
- `recommendation`
- `question`
- `assertion` (when unsafe to promote to a domain Statement)

Claim interiors are **not** world beliefs. Do not treat them as established
facts. `search_memory` excludes Claims unless `include_claims=true`.

Promotion of a Claim into a domain Statement is out of V1 skill scope unless
the user and ontology explicitly support a governed path.

## Decisions

`Decision` is a core ontology **class** (Event subclass) for decision entities —
distinct from Claim `epistemicKind`. Model decisions as entities/statements via
discovery; do not conflate with recommendations.

## Write eligibility (separate decisions)

Before any durable write, treat these as **independent** checks:

| Decision | Question | If no / unclear |
| --- | --- | --- |
| **Authorization** | Did the user ask for, or clearly authorize, durable memory for this content? | Do not write; answer in conversation only. |
| **Relevance** | Is this worth long-term semantic memory (not ephemeral chat noise)? | Do not write; summarize verbally if needed. |
| **Epistemic status** | Is this a world fact, a speech-act, a decision entity, or still exploratory? | Use Claim-shaped modeling when appropriate; do not promote speculation to domain Statements. |
| **Evidence / confidence** | Is support strong enough for a domain Statement, or should confidence stay low / unset? | Prefer Claim, lower `confidence`, ask, or wait — schema fit is not verification. |
| **Schema readiness** | Are class/predicate/object typing known and valid? | Discover ontology or ask; do not invent keys. |

A well-typed proposition can still be false, premature, or unauthorized.
Conversely, proactive memory is allowed when authorization and relevance are
clear (for example the user said “remember that…”), even if the agent
proposed the write — still require epistemic honesty and schema readiness.

### Exploratory conversation

If the user is brainstorming, asking “what if”, or reviewing options without
asking to store: **do not assert**. Offer to store only when they confirm.
