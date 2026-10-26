# Typed Observations

Generic measurements reuse the live `Observation` class and governed
predicates. Confirm keys via discovery when this workflow has not verified them
yet; then reuse for subsequent readings.

## Create

Prefer `assert_batch` (atomic):

1. Entity class `Observation` (stable name pattern is fine).
2. `observationOf` → subject.
3. `observationType` → string (e.g. `height`).
4. `numericValue` → number with `observed_at` = measurement time.
5. `unit` → canonical string (`cm`, `kg`, …).

One numeric measurement per Observation entity. A later reading = **new**
Observation, not supersession of the prior reading (unless the prior was wrong).

## Correct

`correct_statement` on the mistaken statement(s).

## Retrieve series

`query_observations` with `entity_id` (and optional type / time filters).

If `query_observations` is unavailable in this session, disclose the gap —
do not scrape descriptions as a silent substitute.
