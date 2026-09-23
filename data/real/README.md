# data/real/

Real, source-cited FCRA data goes here. Extraction scripts:
`scripts/parse_fcra_parliament.py` (re-run to regenerate; it validates every
run — 26 checks must pass) and `scripts/parse_mha_ar.py` (MHA annual-report
national totals; 6 checks per run).

## Contents (intakes of 2026-09-23)

| File | Rows | What it is |
|---|---|---|
| `fcra_state_year.csv` / `.json` | 464 | State/UT-year FC **received** and **utilized** (INR), plus national totals, per-source. FY 2009-10 – 2024-25 with gaps (see below). |
| `fcra_mha_ar_state_year.csv` / `.json` | 9 | **National** FC received (INR), ALL-INDIA rows from MHA Annual Reports 2012-13 – 2018-19: 2010-11, 2011-12 (×2), 2012-13 (×2), 2013-14 (×2), 2016-17, 2017-18. Conflicting per-report figures kept as separate rows, never merged. |
| `fcra_cancellations.csv` / `.json` | 32 | State-wise FCRA registrations cancelled, 2020 – 22.03.2023 (RS USQ 3253 Annexure-III). Sums to the stated 1,828. |
| `fcra_donor_country.csv` / `.json` | 499 | Donor-country-wise FC received (INR), FY 2016-17 – 2019-20 (official annexure) + 2024-25 top-5 (MHA briefing via BusinessLine). |

Every row carries `source_document`, `source_url`, `table_ref`,
`retrieved_date`, and the original amount + unit. Original Indian-digit
grouping is preserved in `total_fc_original`; `total_fc_inr` is the Decimal
normalization (lakh ×100,000; crore ×10,000,000).

## Coverage by source tier

**Official Parliament / government documents (primary):**
- Lok Sabha USQ 328 (06.08.2013): state-wise received 2009-10, 2010-11, 2011-12 (Rs lakhs) + reporting NGO counts. 2011-12 flagged provisional in source.
- Rajya Sabha SQ 304 (24.03.2021): state-wise received 2016-17 – 2019-20 (exact Rs) + full donor-country tables 2016-17 – 2019-20. 2019-20 is PARTIAL (ARs filed as on 16.03.2021; deadline extended to 30.06.2021).
- Lok Sabha USQ 457 (15.09.2020): national received totals 2016-17 – 2018-19 (Rs cr). The utilized column was illegible in extraction — excluded, not guessed.
- Rajya Sabha USQ 3253 (29.03.2023): state-wise received AND utilized 2019-20 – 2021-22 (Rs cr) + cancellations 2020–22.03.2023.
- PIB backgrounder (22.07.2026): national 2024-25 — ~16,200 associations, ~Rs 22,963 cr.

**MHA Annual Reports (primary, national-only):**
- AR 2012-13: national received 2010-11 (Rs 10,334.11 cr, 22,735 assns) and 2011-12 (Rs 9,423.34 cr, 14,391 assns, till 31.12.2012).
- AR 2013-14: national received 2011-12 (Rs 11,550.78 cr — revises the AR 2012-13 figure) and 2012-13 (Rs 10,875.06 cr, till 31.03.2014).
- AR 2014-15: national received 2012-13 (Rs 11,909.07 cr — revises the AR 2013-14 figure) and 2013-14 (Rs 13,813.068 cr, till 31.12.2014).
- AR 2015-16: national received 2013-14 (Rs 12,980 cr — differs from the AR 2014-15 figure; kept as a separate per-source row).
- AR 2017-18: national received 2016-17 ("over Rs 15,182 crore", document's own qualifier kept).
- AR 2018-19: national received 2017-18 ("over Rs 16,881 crore approx.", qualifiers kept).
- Negative: NO annual report from 2012-13 through 2024-25 contains a state-wise FC table; ARs 2019-20–2024-25 carry disposal stats only, and AR 2016-17 has no FCRA data at all. See `docs/DATA_SOURCES.md`.

**Press reporting of official briefings (secondary, clearly labelled):**
- BusinessLine (19.09.2026) on MHA briefing to the JPC: 2024-25 state receipts for Delhi / Karnataka / Maharashtra / Tamil Nadu, state-wise active-NGO counts, national 2015-16 and 2024-25 totals, top-5 donor countries 2024-25.
- Note the discrepancy the data keeps, not reconciles: BusinessLine says Rs 22,974 cr received in 2024-25; PIB says ~Rs 22,963 cr. Both are present as separate per-source rows.

## Honesty notes (read before using)

1. **Aggregate only.** This is state-year and country-year aggregate data, NOT name-level donor→recipient Form FC-4 flow data. The bulk name-level route via fcraonline.nic.in was genuinely attempted on 2026-09-23 and failed (see `docs/DATA_SOURCES.md`); the portal does not serve bulk rows to plain GETs.
2. **Conflicting sources are never merged.** E.g. 2019-20 received exists per-state in both RS SQ 304 (partial) and RS USQ 3253; both rows are kept with their own provenance. Compare them, don't average them.
3. **2019-20 is covered twice and both copies are partial/dated differently** (ARs as on 16.03.2021 vs ARs as on 22.03.2023) — the later source supersedes for that year but the earlier row is retained for audit.
4. **Utilized can exceed received** in RS USQ 3253: utilization comes from FC-4 annual returns and includes opening balances / prior-year funds.
5. **Gaps with no state-wise public data found yet:** 2012-13, 2013-14, 2014-15, 2015-16, 2022-23, 2023-24. National-only anchors: 2012-13 and 2013-14 (two per-source MHA AR figures each — the reports revised their own numbers as more returns were filed), 2015-16 (Rs 17,832 cr, BusinessLine/MHA), 2024-25 (two per-source figures, see above). The MHA annual-report route for state-level data is exhausted, not merely untried.
6. **Excluded, not guessed:** LS USQ 328 Annexure-III (2011-12) Andaman & Nicobar row extracted as "10 10" — amount ambiguous, excluded. Its implied value (Rs 489.15 lakh) falls out of the document's own arithmetic and is noted, not used as data.
7. Donor-country tables exclude donor details below Rs 20,000 per Form FC-4 (per the source's own footnote). "India" appears as a donor country in RS SQ 304 — transcribed as printed.
8. Real and sample rows are NEVER mixed: the app reads sample rows from `data/sample/` and real rows from here, and the UI labels which is which.

## Validation

`scripts/parse_fcra_parliament.py` runs 26 checks on every generation:
- `(original amount × unit) == total_fc_inr` for all 963 amount rows;
- no duplicate `(state, financial_year, metric, source_url)` keys;
- every transcribed table sums to its document's stated total (LS328 within the document's own Rs 1,000 rounding artifact; all RS304/donor tables to the paisa);
- row counts per official year (34 states for RS3253/RS304 full years; 33 for LS328 2009-10 where the document lists no Daman & Diu row; 33 for 2019-20 partial RS304);
- cancellations sum to the stated 1,828.
