#!/usr/bin/env python3
"""Extract national FC receipt figures from MHA Annual Reports (mha.gov.in).

Findings (verified 2026-09-23): NO MHA annual report from 2012-13 through
2024-25 contains a state-wise foreign-contribution receipt table. The FCRA
wing sections carry national receipt totals only (2012-13..2018-19 ARs) or
application-disposal statistics only (2019-20..2024-25 ARs; 2016-17 AR has
no FCRA data at all).

This script transcribes the national totals as verbatim data literals,
normalizes crore -> INR with Decimal, and runs validation checks on every
run. Rows are written as SEPARATE source rows (never merged with the
Parliament-Q&A rows in fcra_state_year.csv).

Usage: python3 scripts/parse_mha_ar.py
Writes: data/real/fcra_mha_ar_state_year.csv and .json
"""
from __future__ import annotations

import csv
import json
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_CSV = ROOT / "data" / "real" / "fcra_mha_ar_state_year.csv"
OUT_JSON = ROOT / "data" / "real" / "fcra_mha_ar_state_year.json"
RETRIEVED = "2026-09-23"
CRORE = Decimal("10000000")

COLUMNS = [
    "state", "financial_year", "metric", "total_fc_inr", "total_fc_original",
    "original_unit", "reporting_associations", "source_document", "source_url",
    "table_ref", "retrieved_date", "notes",
]

# Verbatim figures, transcribed from the PDF text (pdftotext -layout).
# "verbatim_crore" must match the document's printed figure exactly.
# "qualifier" records words like "over"/"approx." that the document itself used.
ROWS = [
    dict(
        financial_year="2010-11", verbatim_crore="10,334.11", qualifier="",
        reporting_associations=22735,
        source_document="MHA Annual Report 2012-13, Chapter XIII (Foreigners Division), para 13.12",
        source_url="https://www.mha.gov.in/sites/default/files/AnnualReport_12_13.pdf",
        table_ref="Para 13.12 narrative (no table): 'The total receipt of foreign contribution reported by 22,735 associations during the year 2010-11 was Rs 10,334.11 crore.'",
        notes="National total only; no state-wise table in this report. 2010-11 also covered state-wise by LS USQ 328 (separate source, separate rows).",
    ),
    dict(
        financial_year="2011-12", verbatim_crore="9,423.34", qualifier="",
        reporting_associations=14391,
        source_document="MHA Annual Report 2012-13, Chapter XIII (Foreigners Division), para 13.12",
        source_url="https://www.mha.gov.in/sites/default/files/AnnualReport_12_13.pdf",
        table_ref="Para 13.12 narrative (no table): 'The total receipt of foreign contribution during 2011-12, as reported by 14,391 associations till 31.12.2012, is Rs 9,423.34 crore.'",
        notes="National total only. Figure is as-reported till 31.12.2012 and was revised upward in the 2013-14 AR as more annual returns were filed (see separate row).",
    ),
    dict(
        financial_year="2011-12", verbatim_crore="11,550.78", qualifier="",
        reporting_associations=22702,
        source_document="MHA Annual Report 2013-14, Chapter XIII (Foreigners Division), para 13.13",
        source_url="https://www.mha.gov.in/sites/default/files/AnnualReport_13_14.pdf",
        table_ref="Para 13.13 narrative (no table): 'The total receipt of Foreign Contributions reported by 22,702 associations during the year 2011-12 was Rs 11,550.78 crore.'",
        notes="National total only. Revises the 2011-12 figure given in the 2012-13 AR (Rs 9,423.34 crore) as more annual returns were filed; kept as a separate per-source row, never merged.",
    ),
    dict(
        financial_year="2012-13", verbatim_crore="10,875.06", qualifier="",
        reporting_associations=16896,
        source_document="MHA Annual Report 2013-14, Chapter XIII (Foreigners Division), para 13.13",
        source_url="https://www.mha.gov.in/sites/default/files/AnnualReport_13_14.pdf",
        table_ref="Para 13.13 narrative (no table): 'The total receipt of Foreign Contribution during 2012-13, as reported by 16,896 associations till 31.03.2014 is Rs 10,875.06 crore.'",
        notes="National total only; fills a gap year (no state-level 2012-13 data anywhere). Figure as-reported till 31.03.2014; revised upward in the 2014-15 AR (see separate row).",
    ),
    dict(
        financial_year="2012-13", verbatim_crore="11,909.07", qualifier="",
        reporting_associations=18519,
        source_document="MHA Annual Report 2014-15, Chapter XIII (Foreigners Division), para 13.14",
        source_url="https://www.mha.gov.in/sites/default/files/AnnualReport_14_15.pdf",
        table_ref="Para 13.14 narrative (no table): 'The total receipt of Foreign Contribution reported by 18,519 associations during the year 2012-13 was Rs 11,909.07 crore.'",
        notes="National total only. Revises the 2012-13 figure given in the 2013-14 AR (Rs 10,875.06 crore) as more annual returns were filed; kept as a separate per-source row.",
    ),
    dict(
        financial_year="2013-14", verbatim_crore="13,813.068", qualifier="",
        reporting_associations=16868,
        source_document="MHA Annual Report 2014-15, Chapter XIII (Foreigners Division), para 13.14",
        source_url="https://www.mha.gov.in/sites/default/files/AnnualReport_14_15.pdf",
        table_ref="Para 13.14 narrative (no table): 'The total receipt of Foreign Contribution during 2013-14 as reported by 16,868 associations till 31.12.2014 is Rs 13,813.068 crore.'",
        notes="National total only; fills a gap year. Figure as-reported till 31.12.2014. The 2015-16 AR gives a different 2013-14 figure (Rs 12,980 crore); kept as separate per-source rows.",
    ),
    dict(
        financial_year="2013-14", verbatim_crore="12,980", qualifier="",
        reporting_associations=None,
        source_document="MHA Annual Report 2015-16, Chapter XIII (Foreigners Division), para 13.20",
        source_url="https://www.mha.gov.in/sites/default/files/AnnualReport_15_16.pdf",
        table_ref="Para 13.20 narrative (no table): 'At present a total of 33,346 associations are registered under FCRA and Rs 12,980 crore have been received in year 2013-14 under FCRA.'",
        notes="National total only; fills a gap year. Differs from the 2014-15 AR's 2013-14 figure (Rs 13,813.068 crore); both are verbatim per-document figures kept as separate rows. '33,346' is registered associations, not the reporting count, so reporting_associations is left null.",
    ),
    dict(
        financial_year="2016-17", verbatim_crore="15,182", qualifier="over",
        reporting_associations=None,
        source_document="MHA Annual Report 2017-18, Chapter XIII (Foreigners Division), para 13.25",
        source_url="https://www.mha.gov.in/sites/default/files/AnnualReport_17_18.pdf",
        table_ref="Para 13.25 narrative (no table): 'foreign contribution of over Rs 15.182 thousand crore was received in the year 2016-17' (24,900 active associations as on 15.03.2018).",
        notes="National total only. '15.182 thousand crore' = Rs 15,182 crore; the document's own word 'over' is preserved as a qualifier. 2016-17 also covered state-wise by RS SQ 304 (separate source, separate rows).",
    ),
    dict(
        financial_year="2017-18", verbatim_crore="16,881", qualifier="over; approx.",
        reporting_associations=None,
        source_document="MHA Annual Report 2018-19, Chapter XIII (Foreigners Division), para 13.23",
        source_url="https://www.mha.gov.in/sites/default/files/AnnualReport_18_19.pdf",
        table_ref="Para 13.23 narrative (no table): 'During the financial year 2017-18 (as on 31.03.2019), foreign contribution of over Rs 16,881 crore approx. was received' (24,572 active associations as on 11.04.2019).",
        notes="National total only. The document's own words 'over' and 'approx.' are preserved as qualifiers. 2017-18 also covered state-wise by RS SQ 304 (separate source, separate rows).",
    ),
]

# Reports checked with NO usable FC receipt figure (documented negatives).
NEGATIVES = {
    "2016-17": "MHA Annual Report 2016-17: no FCRA wing section at all (single incidental mention in a chapter listing).",
    "2019-20": "MHA Annual Report 2019-20, Ch XIII paras 13.25-13.30: application-disposal statistics only; no receipt totals.",
    "2020-21": "MHA Annual Report 2020-21, Ch XII FCRA Wing paras 12.28-12.35: regulatory/amendment narrative; no receipt totals.",
    "2021-22": "MHA Annual Report 2021-22, Ch XII paras 12.24-12.31: disposal statistics (01.04.2021-31.12.2021) only; no receipt totals.",
    "2022-23": "MHA Annual Report 2022-23: FCRA section carries disposal statistics only; no receipt totals.",
    "2023-24": "MHA Annual Report 2023-24, Ch XII FCRA Wing paras 12.31-12.43: disposal statistics only; no receipt totals.",
    "2024-25": "MHA Annual Report 2024-25, Ch XII FCRA Wing paras 12.36-12.49: disposal statistics and rule amendments; no receipt totals.",
}


def parse_crore(s: str) -> Decimal:
    try:
        return Decimal(s.replace(",", ""))
    except InvalidOperation:
        raise ValueError(f"unparseable crore figure: {s!r}")


def build_rows() -> list[dict]:
    out = []
    for r in ROWS:
        crore = parse_crore(r["verbatim_crore"])
        inr = (crore * CRORE).quantize(Decimal("0.01"))
        out.append({
            "state": "ALL-INDIA",
            "financial_year": r["financial_year"],
            "metric": "received",
            "total_fc_inr": format(inr, ".2f"),
            "total_fc_original": r["verbatim_crore"],
            "original_unit": "crore",
            "reporting_associations": r["reporting_associations"],
            "source_document": r["source_document"],
            "source_url": r["source_url"],
            "table_ref": r["table_ref"],
            "retrieved_date": RETRIEVED,
            "notes": r["notes"] + (f" Document qualifier on the figure: '{r['qualifier']}'." if r["qualifier"] else ""),
        })
    return out


def validate(rows: list[dict]) -> None:
    errors: list[str] = []
    # 1. Row count matches literals.
    if len(rows) != len(ROWS):
        errors.append(f"row count {len(rows)} != literals {len(ROWS)}")
    # 2. Conversion identity: total_fc_inr == verbatim_crore * 1e7.
    for lit, row in zip(ROWS, rows):
        expected = (parse_crore(lit["verbatim_crore"]) * CRORE).quantize(Decimal("0.01"))
        if Decimal(row["total_fc_inr"]) != expected:
            errors.append(f"{row['financial_year']}/{row['source_document'][:30]}: conversion mismatch")
        if row["total_fc_original"] != lit["verbatim_crore"]:
            errors.append(f"{row['financial_year']}: verbatim figure altered")
    # 3. No duplicate (state, FY, metric, source) keys.
    keys = [(r["state"], r["financial_year"], r["metric"], r["source_document"]) for r in rows]
    if len(set(keys)) != len(keys):
        errors.append("duplicate (state, FY, metric, source) keys")
    # 4. Column set exact.
    for r in rows:
        if list(r.keys()) != COLUMNS:
            errors.append(f"column mismatch on {r['financial_year']}")
            break
    # 5. Units and years sane.
    for r in rows:
        if r["original_unit"] != "crore":
            errors.append(f"unit not crore: {r}")
        if r["metric"] != "received" or r["state"] != "ALL-INDIA":
            errors.append(f"unexpected state/metric: {r}")
        ra = r["reporting_associations"]
        if ra is not None and (not isinstance(ra, int) or ra <= 0):
            errors.append(f"bad reporting_associations: {ra}")
        if r["retrieved_date"] != RETRIEVED:
            errors.append("bad retrieved_date")
        if not r["source_url"].startswith("https://www.mha.gov.in/sites/default/files/"):
            errors.append(f"non-canonical source_url: {r['source_url']}")
    # 6. Known revised pairs both present (we must not silently drop either).
    fy1112 = [r for r in rows if r["financial_year"] == "2011-12"]
    fy1213 = [r for r in rows if r["financial_year"] == "2012-13"]
    fy1314 = [r for r in rows if r["financial_year"] == "2013-14"]
    if len(fy1112) != 2 or len(fy1213) != 2 or len(fy1314) != 2:
        errors.append("expected two per-source rows each for 2011-12, 2012-13, 2013-14")
    if errors:
        raise SystemExit("VALIDATION FAILED:\n" + "\n".join(" - " + e for e in errors))
    print(f"validation OK: {len(rows)} rows, {6} checks passed")


def main() -> None:
    rows = build_rows()
    validate(rows)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(rows)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2, ensure_ascii=False)
    print(f"wrote {OUT_CSV} ({len(rows)} rows)")
    print(f"wrote {OUT_JSON} ({len(rows)} rows)")
    print("documented negatives (no usable FC receipt figure):")
    for k, v in NEGATIVES.items():
        print(f"  AR {k}: {v}")


if __name__ == "__main__":
    sys.exit(main())
