# Data sources — FCRA FLOW

Last updated: 2026-09-23.

## Primary source

- **MHA FCRA dashboard / portal:** https://fcraonline.nic.in/
- **Return form:** Form FC-4 — annual return of foreign contribution received
  and utilised, filed online per Rule 17 of the Foreign Contribution
  (Regulation) Rules, 2011. Filing is mandatory every financial year
  (1 April – 31 March), including NIL returns.
- **Background reference:** MHA FAQ on FCRA filing (Form FC-4),
  https://fcraonline.nic.in/Home/PDF_Doc/fc_faq_04102022.pdf — confirms online
  filing at fcraonline.nic.in and mandatory NIL returns.
- PIB release (2020-09-16, PRID 1655000) confirming annual returns are uploaded
  on the FCRA portal and state-wise registered-association details are public.

## Real-data fetch attempt — 2026-09-23 (honest log)

Goal: pull real, public, bulk FCRA data (association lists / filed annual
returns) using only plain public HTTP fetches at a polite rate. No CAPTCHA
bypass, no login bypass, no paywall circumvention — those are hard standing
rules and were never attempted.

What was tried, in order:

1. `curl` (plain GET, research User-Agent, 30–40s timeouts) from the sandbox:
   - `https://fcraonline.nic.in/` → connection failed / empty reply (exit 52).
   - `https://fcraonline.nic.in/home/pdf_doc/associations.pdf` → same failure.
   - `http://fcraonline.nic.in/` → same failure.
   - Control: `https://example.com` and `http://example.com` → HTTP 200.
     The sandbox egress proxy works; the fcraonline.nic.in host specifically
     does not answer plain requests from this network (empty reply before any
     HTTP status).
2. `browser.open` (fetch-tool path) on `https://fcraonline.nic.in/` → returned
   an empty page (title "FCRA Online Services", no body text). The portal's
   landing page is a JS-driven shell; per-NGO and dashboard data flows through
   interactive POST-backed views, not plain static files.
3. `browser.open` on the known public FAQ PDF
   (`.../Home/PDF_Doc/fc_faq_04102022.pdf`) → **worked** (2,687 lines of text).
   This is a static document, not data, but it grounds the Form FC-4 schema.
4. `browser.open` on `https://fcraonline.nic.in/Home/PDF_Doc/associations.pdf`
   → tool failure, no recovery. Attempt stopped there per the no-retry rule.

**Outcome: 0 real rows obtained.** The portal's bulk data (registered-association
lists, filed annual returns) is served behind interactive/JS dashboard flows;
no clean static bulk file was reachable from this environment. Nothing was
scraped around the failure, and no access control was probed.

## What this means for the repo

- `data/real/` is intentionally empty. `data/sample/sample_fcra.json` (24
  illustrative rows) powers the UI and is labeled SAMPLE everywhere.
- Homepage stats are computed from the sample dataset and labeled "SAMPLE".
- The next step is a browser-based (human-supervised) pass over the MHA
  dashboard's public search to capture legitimately downloadable return
  lists, or an official data request — never a bypass.

## Scripts

- `scripts/fetch_fcra_public.py` — polite plain-GET fetcher for the portal's
  public static documents (NOT yet run successfully against the live portal;
  kept as the documented method for a future network where the host answers).

---

## Real-data intake — 2026-09-23 (aggregate track)

The name-level bulk route via fcraonline.nic.in remains unavailable (see above).
In parallel, a public-document hunt recovered **real aggregate FCRA data from
Parliament Q&A documents and official press** — state-year and donor-country
level, all with per-row provenance. This is REAL data, not sample data, but it
is **aggregate, not name-level Form FC-4 donor→recipient flow data**.

### Extraction

- Script: `scripts/parse_fcra_parliament.py` (re-runnable; 26 validation checks
  must pass — conversion identity, no duplicate keys, every transcribed table
  sums to its document's stated total, per-year row counts, cancellations sum
  to 1,828).
- Outputs: `data/real/fcra_state_year.csv`/`.json` (464 rows),
  `data/real/fcra_cancellations.csv`/`.json` (32 rows),
  `data/real/fcra_donor_country.csv`/`.json` (499 rows).

### Sources (with extracted row counts)

| # | Document | URL | Rows extracted |
|---|---|---|---|
| 1 | Lok Sabha USQ 328, "Funds to NGOs", answered 06.08.2013 | https://xn--i1b5bzbybhfo5c8b4bxh.xn--11b7cb3a6a.xn--h2brj9c/MHA1/Par2017/pdfs/par2013-pdfs/ls-060813/328.pdf | 100 state rows (2009-10, 2010-11, 2011-12) + 3 national totals, Rs in Lakhs, with reporting-NGO counts |
| 2 | Rajya Sabha SQ 304, "Foreign Funds Received by NGOs", answered 24.03.2021 | https://www.scribd.com/document/500156210/Foreign-Contribution-List-MHA (Scribd copy of official annexure) | 135 state rows + 4 national totals (2016-17–2019-20, exact Rs); 490 donor-country rows + 4 totals (2016-17–2019-20) |
| 3 | Lok Sabha USQ 457, "Foreign Funding to NGOs", answered 15.09.2020 | https://sansad.in/getFile/loksabhaquestions/annex/174/AU457.pdf?source=pqals | 3 national received totals (2016-17–2018-19), Rs cr |
| 4 | Rajya Sabha USQ 3253, "Funds Received by NGOs from Abroad", answered 29.03.2023 | https://www.mha.gov.in/MHA1/Par2017/pdfs/par2023-pdfs/RS29032023/3253.pdf | 102 state received + 102 state utilized rows (2019-20–2021-22), Rs cr; 32 state cancellation counts (2020–22.03.2023) |
| 5 | BusinessLine, "FCRA registered NGOs down by half in last 10 years…", 19.09.2026 (MHA briefing to the JPC) | https://www.thehindubusinessline.com/news/fcra-registered-ngos-down-by-half-in-last-10-years-contribution-rises-from-17832-cr-to-22974-cr/article71483639.ece/amp/ | 4 state 2024-25 receipts, 6 state active-NGO counts, 4 national rows (2015-16, 2024-25), 5 donor-country rows — secondary source, labelled as such |
| 6 | PIB backgrounder "Transparency, Sovereignty and Democratic Accountability", 22.07.2026 | https://www.pib.gov.in/PressReleasePage.aspx?PRID=2287897&reg=48&lang=1 | 1 national 2024-25 row (~16,200 associations, ~Rs 22,963 cr) |

### Discrepancies kept, not reconciled

- **2024-25 national receipts:** BusinessLine/MHA-JPC-briefing says Rs 22,974 cr; PIB says ~Rs 22,963 cr. Both rows retained per-source.
- **2019-20 state received:** covered by both RS SQ 304 (partial — ARs as on 16.03.2021) and RS USQ 3253 (ARs as on 22.03.2023). Both rows retained per-source; the later source is the more complete one.
- **2011-12 Andaman & Nicobar row (LS USQ 328 Annexure-III)** extracted as "10 10" — ambiguous, excluded. The document's own arithmetic implies Rs 489.15 lakh for it; noted, not used.
- LS USQ 328 stated totals differ from state-row sums by 0.01 lakh (Rs 1,000) in 2009-10 and 2010-11 — a rounding artifact in the source document, documented in the notes field.
- LS USQ 457's "Total FC utilized" column was illegible in text extraction — excluded, not guessed.

### Failed / partial routes (2026-09-23)

- fcraonline.nic.in bulk name-level ingestion: failed (see above), 0 rows.
- No complete authoritative state-wise table found for 2022-23, 2023-24, or (state-level) 2012-13–2015-16. National-only anchors: 2015-16 Rs 17,832 cr (BusinessLine/MHA), 2024-25 two per-source figures (see above).
- Donor-country tables for 2022-23+ not found in public documents.

## Real-data intake — MHA Annual Reports — 2026-09-23

**Method:** all 20 MHA annual reports listed at
`https://www.mha.gov.in/en/documents/annual-reports` were located; the 11
covering FY 2012-13 through FY 2024-25 were downloaded (plain GET, polite
rate) and their full text extracted with `pdftotext -layout`. The Foreigners
Division / FCRA Wing chapter of each was read in full.

**Headline finding — documented negative:** NO MHA annual report from
2012-13 through 2024-25 contains a state-wise foreign-contribution receipt
table. The FCRA Wing sections carry **national receipt totals only** (in the
2012-13 through 2018-19 reports) or **application-disposal statistics only**
(2019-20 through 2024-25 reports; the 2016-17 report has no FCRA data at
all). The state-wise tables seen in parliamentary documents (e.g. LS USQ
328's 2009-10 annexure) were parliamentary disclosures, not an annual-report
feature.

**Extracted (new data):** 9 national-total rows → `data/real/fcra_mha_ar_state_year.csv`/`.json`
(columns identical to `fcra_state_year.csv`; `state` = ALL-INDIA). Extraction
script `scripts/parse_mha_ar.py` (re-runnable; 6 validation checks per run:
verbatim-figure preservation, crore→INR conversion identity, no duplicate
(state, FY, metric, source) keys, column-set, unit/year sanity, revised-pair
completeness).

| AR | FY of figure | Verbatim figure | Reported by |
|---|---|---|---|
| 2012-13, Ch XIII para 13.12 | 2010-11 | Rs 10,334.11 crore | 22,735 associations |
| 2012-13, Ch XIII para 13.12 | 2011-12 | Rs 9,423.34 crore | 14,391 associations, till 31.12.2012 |
| 2013-14, Ch XIII para 13.13 | 2011-12 | Rs 11,550.78 crore | 22,702 associations (revises the AR 2012-13 figure as more ARs were filed) |
| 2013-14, Ch XIII para 13.13 | 2012-13 | Rs 10,875.06 crore | 16,896 associations, till 31.03.2014 |
| 2014-15, Ch XIII para 13.14 | 2012-13 | Rs 11,909.07 crore | 18,519 associations (revises the AR 2013-14 figure) |
| 2014-15, Ch XIII para 13.14 | 2013-14 | Rs 13,813.068 crore | 16,868 associations, till 31.12.2014 |
| 2015-16, Ch XIII para 13.20 | 2013-14 | Rs 12,980 crore | — (33,346 registered, not the reporting count; kept as a separate per-source row against the AR 2014-15 figure above) |
| 2017-18, Ch XIII para 13.25 | 2016-17 | "over Rs 15.182 thousand crore" (= Rs 15,182 crore; document's own word "over" preserved as qualifier) | 24,900 active as on 15.03.2018 |
| 2018-19, Ch XIII para 13.23 | 2017-18 | "over Rs 16,881 crore approx." (document's own words preserved as qualifiers) | 24,572 active as on 11.04.2019; figure as on 31.03.2019 |

Canonical source URLs (all `https://www.mha.gov.in/sites/default/files/`):
`AnnualReport_12_13.pdf`, `AnnualReport_13_14.pdf`, `AnnualReport_14_15.pdf`,
`AnnualReport_15_16.pdf`, `AnnualReport_17_18.pdf`, `AnnualReport_18_19.pdf`.
Retrieved 2026-09-23. Local copies of all 11 checked PDFs are kept under
`~/workspace/fcra-flow-audit/mha_ar/` (not committed — working copies for audit).

**Documented negatives (no usable FC receipt figure):**
- AR 2016-17: no FCRA Wing section at all.
- AR 2019-20 (Ch XIII 13.25–13.30), AR 2021-22 (Ch XII 12.24–12.31), AR 2022-23, AR 2023-24 (Ch XII 12.31–12.43): application-disposal statistics only.
- AR 2020-21 (Ch XII 12.28–12.35), AR 2024-25 (Ch XII 12.36–12.49): regulatory narrative / rule amendments; no receipt totals.

**Gap status after this intake:** state-level data for 2012-13 – 2015-16 and
2022-23 – 2023-24 remains unfound in any public document; the MHA annual
reports add national-only anchors for 2012-13 (two per-source figures) and
2013-14 (two per-source figures). The earlier "Failed / partial routes" note
above is updated accordingly: the AR route is exhausted for these years, not
merely untried.
