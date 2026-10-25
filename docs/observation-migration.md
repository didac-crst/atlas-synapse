# Production Observation migration (gated)

**Not run automatically.** Code deploy and MCP verification must succeed before any
production mutation.

## Prerequisites

1. Deploy `fix/ontology-observations-reliability` (or merged main).
2. Relevant tests green.
3. MCP agent surface shows `assert_batch` and `challenge_ontology_review`.
4. Propose/apply typed Observation predicates via governance
   (`OBSERVATION_PREDICATE_PROPOSALS`).
5. Verified database backup.
6. Inventory confirms 65 Observation IDs (Siena 15h/16w, Elma 15h/19w).

## Commands

Dry-run inventory/plan (safe):

```bash
python scripts/migrate_typed_observations.py \
  --write-inventory /tmp/obs-inventory.json
```

Enrich in place (after backup):

```bash
python scripts/migrate_typed_observations.py \
  --execute --i-have-backup \
  --actor-key <ops-actor>
```

Only after enrichment verification, clean redundant Person descriptions
(retract, never delete):

```bash
python scripts/migrate_typed_observations.py \
  --cleanup-descriptions --execute --i-have-backup \
  --actor-key <ops-actor>
```

## Post-checks

- 65 Observation IDs unchanged.
- Each has `observationOf`, `observationType`, `numericValue`, `unit`.
- `observed_at` unchanged vs inventory.
- 0 orphans; no new duplicates.
- Person biography `description` retained; bulk dumps retracted.
- Open cardinality conflicts on those descriptions closed/resolved.
