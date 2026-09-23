# data/real/

Real, source-cited Form FC-4 filing rows go here once bulk ingestion from the
MHA FCRA dashboard (https://fcraonline.nic.in/) ships.

**Status (2026-09-23): empty.** A genuine attempt to fetch public data from
fcraonline.nic.in was made on 2026-09-23 and failed (see
`docs/DATA_SOURCES.md` for the full attempt log — URLs, methods, outcomes).
No rows were obtained, so this directory holds none.

Rules for this directory:
- One row per donor filing, per-row `source_url` provenance (no bulk blobs
  without provenance).
- Real and sample rows are NEVER mixed silently; the app reads sample rows
  from `data/sample/` and real rows from here, and the UI labels which is
  which.
- `ingestion_log.json` (when ingestion ships) records, per batch: source URL,
  retrieval timestamp, SHA-256 of the fetched payload, row count.
