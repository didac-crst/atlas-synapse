# Governance, provenance, recovery

## Capabilities and gates

Visibility ≠ authorization. Even listed tools may reject writes without the
right actor capabilities. Ontology apply revalidates at commit; there is no
force path.

Prefer `dry_run=true` to preview mutations. Dry-run does not persist knowledge
writes.

## Provenance

Sources and evidence are first-class. Prefer attaching evidence when the user
provides a source. Unknown reliability stays null — it is not “perfect”.

Agent-surface ChatGPT usually does not see low-level provenance ingest tools;
do not invent provenance IDs. Capture what the available tools allow; escalate
when richer provenance APIs are required.

## Quality / supersession repair

If responses surface memory-quality issues about supersession integrity, use
`repair_supersession_integrity` with the given `issue_id` and an explicit
`successor_statement_id`. Do not guess successors.

## Governance error recovery

1. Read stable `error_code` / outcome fields.
2. Fix inputs (unknown class → discover; ambiguity → clarify; conflict →
   explicit resolve path).
3. Challenge ontology review only with new rationale/evidence via
   `challenge_ontology_review`.
4. Never invent “success” after a rejection.
