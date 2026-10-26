# Document content (text revisions)

Use existing provenance content tools to attach article bodies or OCR
transcriptions to a Document — **do not** invent a parallel document store or
re-assert the same semantic facts.

## Formats

| Supported `content_format` | Notes |
| --- | --- |
| `text` | Plain transcription (e.g. OCR); preserves exact original |
| `html` | Exact HTML preserved; canonical Markdown generated |
| `markdown` | Markdown body |

**Not supported:** PDF or other binary blobs via MCP. If the user only has a
PDF, store the OCR/transcription text (keep the original language) and disclose
that the binary file itself was not ingested.

## Attach OCR / transcription to an existing Document

1. Confirm the Document `entity_id` (from prior create / `search_memory`).
2. Call `ingest_source_content` with:
   - `document_entity_id` = that Document
   - `source` identity (`source_system` + `external_id`, or title/uri/hash)
   - `content` = full transcription text
   - `content_format` = `text` (or `html` / `markdown` when appropriate)
   - `request_id` + `idempotency_key` (no `actor_key`)
3. Verify with `get_source_content` (`document_entity_id`, `include_original=true`)
   so original language text is intact.
4. Optional: `search_source_content` for passage locators.

`ingest_source_content` is provenance-only: it does **not** create domain
Statements. Prefer this over dumping OCR into `description` or duplicating
already-stored facts.

`ensure_source` is optional when you need a stable `source_id` before ingest;
ingest can create/reuse the source via the embedded `source` object.

## Evidence rows

`add_evidence` (statement ↔ source/excerpt) may remain advanced-only. Storing
document **body** text does not require it. Do not claim statement-level
evidence was attached unless `add_evidence` succeeded in this session.
