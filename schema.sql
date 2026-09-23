-- FCRA FLOW schema: Foreign Contribution (Regulation) Act disclosure tracker.
-- Every figure traces to a cited public source (MHA fcraonline.nic.in,
-- Form FC-4 annual returns). Sample and real rows are never mixed silently.

CREATE TABLE IF NOT EXISTS ingestion_ledger (
  id SERIAL PRIMARY KEY,
  source_name TEXT NOT NULL,
  source_url TEXT NOT NULL,
  retrieved_at TIMESTAMPTZ NOT NULL,
  sha256 TEXT NOT NULL,
  row_count INTEGER NOT NULL,
  dataset_kind TEXT NOT NULL DEFAULT 'real'  -- 'real' or 'sample'
);

-- One row per donor filing per NGO per financial year.
CREATE TABLE IF NOT EXISTS filings (
  id SERIAL PRIMARY KEY,
  filing_ref TEXT NOT NULL,          -- e.g. F001 (sample) or portal reference
  ngo_name TEXT NOT NULL,
  fcra_reg_no_masked TEXT NOT NULL,  -- masked like 12XXX8893X; full numbers never stored
  donor_name TEXT NOT NULL,
  donor_country TEXT NOT NULL,
  amount_inr BIGINT NOT NULL,        -- 0 = NIL filing row
  fy TEXT NOT NULL,                  -- e.g. 2022-23
  purpose TEXT,
  source_url TEXT NOT NULL,
  filing_date DATE,
  dataset_kind TEXT NOT NULL DEFAULT 'real',
  ledger_id INTEGER REFERENCES ingestion_ledger(id),
  UNIQUE (filing_ref, dataset_kind)
);
CREATE INDEX IF NOT EXISTS idx_filings_ngo ON filings(ngo_name);
CREATE INDEX IF NOT EXISTS idx_filings_donor ON filings(donor_name);
CREATE INDEX IF NOT EXISTS idx_filings_fy ON filings(fy);
CREATE INDEX IF NOT EXISTS idx_filings_kind ON filings(dataset_kind);

-- Mechanical flag runs: which rule fired on which filing, with the exact
-- formula text, so the UI can always show "rule shown next to flag".
CREATE TABLE IF NOT EXISTS flag_runs (
  id SERIAL PRIMARY KEY,
  filing_id INTEGER NOT NULL REFERENCES filings(id),
  flag_id TEXT NOT NULL,             -- SPIKE | CONCENTRATION | DORMANT_REVIVAL
  flag_name TEXT NOT NULL,
  formula TEXT NOT NULL,
  detail TEXT NOT NULL,
  computed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (filing_id, flag_id)
);
CREATE INDEX IF NOT EXISTS idx_flag_runs_flag ON flag_runs(flag_id);

-- Flag definitions (mirrors data/flags.json).
CREATE TABLE IF NOT EXISTS flag_definitions (
  flag_id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  rule TEXT NOT NULL,
  formula TEXT NOT NULL
);
