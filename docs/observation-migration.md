# Production Observation migration (gated)

**Not run automatically.** Distinguish:

| Operation | Risk | When |
|-----------|------|------|
| **Code deploy** | App/MCP behavior | After review + tests |
| **Ontology apply** | Live predicate catalog | After deploy + MCP verify |
| **Data enrichment** | Knowledge graph rows | After fresh verified backup |
| **Description cleanup** | Retracts Person narratives | After enrichment verification |

## Prerequisites

1. Deploy `fix/ontology-observations-reliability` (or merged main) from **committed**
   tree only (do not bake uncommitted KI WIP into the image).
2. Relevant tests green + HTTP smoke (`scripts/smoke_deploy.sh`).
3. MCP agent surface shows `assert_batch` and `challenge_ontology_review`.
4. Propose/apply typed Observation predicates via governance
   (`OBSERVATION_PREDICATE_PROPOSALS`).
5. **Backup verification** (operator assertion alone is not enough):
   - Check latest nightly: `/mnt/it-ops/satellite/backups/postgres-timescale/latest.json`
   - Compare backup UTC time to `max(created_at)` of Siena/Elma Observations.
   - If the nightly predates those rows, take a **fresh** `atlas_synapse` dump and
     verify size + `pg_restore --list` before `--execute`.
6. Write a machine-readable pre-migration inventory (`--write-inventory`).
7. Inventory confirms 65 Observation IDs (Siena 15h/16w, Elma 15h/19w).

## Backup verification commands

```bash
# Nightly manifest
cat /mnt/it-ops/satellite/backups/postgres-timescale/latest.json

# Fresh single-DB dump (example)
STAMP=$(date -u +%Y%m%dT%H%M%SZ)
OUT=/srv/satellite/backups/atlas-synapse/atlas_synapse-pre-obs-migrate-${STAMP}.dump
docker exec satellite-postgres-timescale \
  pg_dump -U atlas_synapse_app -d atlas_synapse --format=custom -f /tmp/atlas_synapse.dump
docker cp satellite-postgres-timescale:/tmp/atlas_synapse.dump "$OUT"
pg_restore --list "$OUT" | head
sha256sum "$OUT"
```

Pass the dump path to the migrator:

```bash
python scripts/migrate_typed_observations.py \
  --execute --i-have-backup \
  --backup-path "$OUT" \
  --require-backup-after 2026-10-25T10:00:00+00:00 \
  --actor-key <ops-actor>
```

`--require-backup-after` fails closed unless the backup file mtime (or embedded
stamp in the filename) is strictly after that timestamp.

## Commands

Dry-run inventory/plan (safe):

```bash
python scripts/migrate_typed_observations.py \
  --write-inventory /tmp/obs-inventory.json
```

Enrich in place (idempotent; preserves entity IDs):

```bash
python scripts/migrate_typed_observations.py \
  --execute --i-have-backup \
  --backup-path "$OUT" \
  --require-backup-after <ISO-UTC-after-observations-exist> \
  --actor-key <ops-actor>
```

Only after enrichment verification, clean redundant Person descriptions
(retract, never delete):

```bash
python scripts/migrate_typed_observations.py \
  --cleanup-descriptions --execute --i-have-backup \
  --backup-path "$OUT" \
  --require-backup-after <ISO-UTC-after-observations-exist> \
  --actor-key <ops-actor>
```

## Post-checks

- 65 Observation IDs unchanged (diff inventory before/after).
- Each has `observationOf`, `observationType`, `numericValue`, `unit`.
- `observed_at` unchanged vs inventory.
- 0 orphans; no new duplicates.
- Person biography `description` retained; bulk dumps retracted.
- Open cardinality conflicts on those descriptions closed/resolved.
- Rerun enrichment is a no-op (idempotent reuse counters).
