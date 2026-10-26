# Facts, Claims, Decisions

## Domain Statements (facts)

Subject–predicate–object beliefs about the world. Use `assert_statement` /
`assert_batch` when evidence and ontology allow. These are what ordinary
retrieval returns.

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

## Avoid unnecessary assertions

Store when the user wants durable memory **and** the proposition is
well-typed. Prefer clarifying questions, dry-run, or Claim-shaped capture when
the content is speculative, advisory, or underspecified.
