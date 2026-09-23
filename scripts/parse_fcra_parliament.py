#!/usr/bin/env python3
"""Extract REAL public FCRA aggregate data from Parliament Q&A documents + press.

Reproducibility note: the source tables were read from public documents on
2026-09-23 (URLs in docs/DATA_SOURCES.md). This script holds the transcribed
tables as data literals (amount strings copied verbatim, Indian digit grouping
kept) and emits normalized CSV/JSON with per-source provenance rows.

Hard rules baked in:
- One row per (state, financial_year, metric, source). Conflicting sources are
  NEVER merged; each keeps its own row (SIR-WATCH convention).
- Ambiguous cells are excluded and logged, never guessed.
- Amounts: original value + unit preserved; normalized to INR via Decimal.

Run:  python3 scripts/parse_fcra_parliament.py
Out:   data/real/fcra_state_year.csv / .json
       data/real/fcra_cancellations.csv / .json
       data/real/fcra_donor_country.csv / .json
"""

import csv
import json
import os
import sys
from decimal import Decimal, ROUND_HALF_UP

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REAL = os.path.join(BASE, "data", "real")
TODAY = "2026-09-23"

EXCLUDED = []  # (reason, detail) for the honesty log


def inr(amount_str, unit):
    """Normalize a verbatim amount string to INR (Decimal, 2dp)."""
    d = Decimal(amount_str.replace(",", "").strip())
    if unit == "lakh":
        d = d * Decimal("100000")
    elif unit == "crore":
        d = d * Decimal("10000000")
    elif unit == "rupee":
        pass
    else:
        raise ValueError("unknown unit: %r" % unit)
    return d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


# ----------------------------------------------------------------------------
# SOURCE REGISTRY
# ----------------------------------------------------------------------------
SOURCES = {
    "ls328": {
        "document": "Lok Sabha Unstarred Question No. 328, 'Funds to NGOs', "
                    "answered 06.08.2013 (Ministry of Home Affairs, "
                    "Shri Mullappally Ramachandran)",
        "url": "https://xn--i1b5bzbybhfo5c8b4bxh.xn--11b7cb3a6a.xn--h2brj9c/"
               "MHA1/Par2017/pdfs/par2013-pdfs/ls-060813/328.pdf",
        "notes": "State-wise FC received, Rs in Lakhs. 2011-12 flagged in the "
                 "document itself as 'some more data is still under compilation'. "
                 "Source-arithmetic note: the document's stated totals differ "
                 "from the sum of its state rows by 0.01 lakh (Rs 1,000) in "
                 "2009-10 and 2010-11 -- a rounding artifact in the source. "
                 "In 2011-12 the stated total exceeds the sum of included "
                 "state rows by Rs 489.15 lakh, which per the document's own "
                 "arithmetic is the excluded Andaman & Nicobar row.",
    },
    "rs304": {
        "document": "Rajya Sabha Starred Question No. 304, 'Foreign Funds Received "
                    "by NGOs', answered 24.03.2021 (MoS Home, Shri Nityanand Rai)",
        "url": "https://www.scribd.com/document/500156210/"
               "Foreign-Contribution-List-MHA",
        "notes": "Scribd copy of the official annexure. Annexure-I: state-wise "
                 "FC received in Rupees. Annexure-II: donor-country-wise FC in "
                 "Rupees (excludes donor details < Rs 20,000 per FC-4). "
                 "2019-20 tables are PARTIAL: ARs filed as on 16.03.2021; filing "
                 "deadline extended to 30.06.2021.",
    },
    "ls457": {
        "document": "Lok Sabha Unstarred Question No. 457, 'Foreign Funding to NGOs', "
                    "answered 15.09.2020 (MoS Home, Shri Nityanand Rai)",
        "url": "https://sansad.in/getFile/loksabhaquestions/annex/174/"
               "AU457.pdf?source=pqals",
        "notes": "National 'Total FC received' (Rs in Crore). The 'Total FC "
                 "utilized' column was illegible in text extraction and is "
                 "excluded, not guessed.",
    },
    "rs3253": {
        "document": "Rajya Sabha Unstarred Question No. 3253, 'Funds Received by "
                    "NGOs from Abroad', answered 29.03.2023 (MoS Home, "
                    "Shri Nityanand Rai)",
        "url": "https://www.mha.gov.in/MHA1/Par2017/pdfs/par2023-pdfs/"
               "RS29032023/3253.pdf",
        "notes": "Annexure-I: state-wise FC RECEIVED (Rs Cr). Annexure-II: "
                 "state-wise FC UTILIZED (Rs Cr). Based on Annual Returns "
                 "submitted as on 22.03.2023. Annexure-III: cancellations "
                 "2020 to 22.03.2023 (state counts, not amounts).",
    },
    "bl_jpc": {
        "document": "The Hindu BusinessLine, 'FCRA registered NGOs down by half in "
                    "last 10 years; contribution rises from Rs 17,832 cr to "
                    "Rs 22,974 cr', published 19.09.2026 (MHA briefing to the "
                    "Joint Parliamentary Committee on the FCRA Amendment Bill)",
        "url": "https://www.thehindubusinessline.com/news/fcra-registered-ngos-"
               "down-by-half-in-last-10-years-contribution-rises-from-17832-cr-"
               "to-22974-cr/article71483639.ece/amp/",
        "notes": "Press report of an official MHA briefing (Home Secretary "
                 "Govind Mohan to JPC). Figures are as reported by the outlet.",
    },
    "pib_fcra": {
        "document": "PIB Backgrounder 'Transparency, Sovereignty and Democratic "
                    "Accountability' (FCRA), posted 22.07.2026 by PIB Delhi",
        "url": "https://www.pib.gov.in/PressReleasePage.aspx?PRID=2287897"
               "&reg=48&lang=1",
        "notes": "Official PIB backgrounder. National 2024-25 figures differ "
                 "slightly from the BusinessLine JPC-briefing figures; both "
                 "kept as separate per-source rows.",
    },
}

# ----------------------------------------------------------------------------
# STATE-YEAR ROWS  (state, financial_year, metric, amount_str, unit,
#                   reporting_associations, table_ref, notes)
# metric: 'received' | 'utilized'
# ----------------------------------------------------------------------------
STATE_ROWS = []

# ---- LS USQ 328 (6.8.2013): Rs in Lakhs, with "Reported" NGO counts ----
_LS328_2009_10 = [
    ("Delhi", 1426, "181878.46"), ("Tamil Nadu", 3337, "166799.68"),
    ("Andhra Pradesh", 2629, "132847.41"), ("Karnataka", 1613, "105046.20"),
    ("Maharashtra", 1852, "92677.17"), ("Kerala", 1687, "89298.50"),
    ("West Bengal", 1935, "56063.98"), ("Gujarat", 1064, "39428.92"),
    ("Uttar Pradesh", 1348, "21837.47"), ("Orissa", 1260, "21464.14"),
    ("Jharkhand", 469, "15965.02"), ("Himachal Pradesh", 114, "14507.04"),
    ("Madhya Pradesh", 448, "14285.86"), ("Bihar", 848, "14171.99"),
    ("Rajasthan", 405, "12785.62"), ("Uttarakhand", 285, "10738.83"),
    ("Assam", 256, "9321.11"), ("Punjab", 115, "8737.86"),
    ("Meghalaya", 131, "6546.31"), ("Chhattisgarh", 232, "6498.64"),
    ("Manipur", 296, "3681.38"), ("Pondicherry", 85, "3299.96"),
    ("Nagaland", 83, "2903.15"), ("Haryana", 117, "2807.58"),
    ("Jammu & Kashmir", 81, "2617.88"), ("Goa", 108, "2439.45"),
    ("Andaman & Nicobar Islands", 12, "1072.35"), ("Chandigarh", 42, "912.85"),
    ("Arunachal Pradesh", 24, "904.14"), ("Mizoram", 34, "838.43"),
    ("Tripura", 33, "724.21"), ("Sikkim", 8, "311.23"),
    ("Dadra & Nagar Haveli", 14, "109.26"),
]
_LS328_2010_11 = [
    ("Delhi", 1453, "201729.78"), ("Tamil Nadu", 3419, "155857.33"),
    ("Andhra Pradesh", 2710, "117900.95"), ("Karnataka", 1637, "100158.04"),
    ("Maharashtra", 2094, "91535.63"), ("Kerala", 1662, "87341.84"),
    ("West Bengal", 2032, "65172.07"), ("Gujarat", 1149, "36378.12"),
    ("Uttar Pradesh", 1235, "25740.86"), ("Orissa", 1322, "21236.94"),
    ("Madhya Pradesh", 467, "14564.96"), ("Bihar", 838, "14410.93"),
    ("Rajasthan", 431, "14133.46"), ("Jharkhand", 454, "13462.99"),
    ("Himachal Pradesh", 106, "12874.61"), ("Uttarakhand", 282, "11671.90"),
    ("Punjab", 125, "8723.66"), ("Assam", 254, "8627.07"),
    ("Chhattisgarh", 230, "5724.55"), ("Manipur", 322, "4683.44"),
    ("Meghalaya", 126, "4070.67"), ("Jammu & Kashmir", 93, "3856.63"),
    ("Pondicherry", 80, "3052.61"), ("Nagaland", 96, "2381.68"),
    ("Haryana", 119, "2230.20"), ("Goa", 101, "1874.96"),
    ("Chandigarh", 47, "1278.64"), ("Arunachal Pradesh", 21, "996.55"),
    ("Tripura", 24, "749.13"), ("Sikkim", 10, "641.61"),
    ("Andaman & Nicobar Islands", 12, "627.91"), ("Mizoram", 30, "500.44"),
    ("Dadra & Nagar Haveli", 11, "165.34"), ("Daman & Diu", 1, "2.94"),
]
_LS328_2011_12 = [
    ("Delhi", 1417, "206757.82"), ("Tamil Nadu", 3220, "158468.63"),
    ("Andhra Pradesh", 2436, "118002.11"), ("Karnataka", 1589, "104073.60"),
    ("Maharashtra", 1942, "103315.22"), ("Kerala", 1593, "89135.72"),
    ("West Bengal", 2024, "70883.48"), ("Gujarat", 1004, "34532.43"),
    ("Orissa", 1291, "22400.67"), ("Uttar Pradesh", 1169, "22230.62"),
    ("Bihar", 809, "16335.76"), ("Madhya Pradesh", 448, "14126.52"),
    ("Jharkhand", 444, "13676.29"), ("Rajasthan", 424, "12696.88"),
    ("Uttarakhand", 269, "11376.02"), ("Assam", 248, "11357.08"),
    ("Punjab", 130, "8820.39"), ("Himachal Pradesh", 103, "7623.33"),
    ("Chhattisgarh", 228, "5918.18"), ("Meghalaya", 126, "4914.07"),
    ("Manipur", 279, "4447.03"), ("Jammu & Kashmir", 96, "3095.60"),
    ("Nagaland", 84, "2785.68"), ("Pondicherry", 80, "2697.15"),
    ("Goa", 75, "1530.25"), ("Haryana", 109, "2359.16"),
    ("Chandigarh", 50, "1273.82"), ("Arunachal Pradesh", 27, "911.17"),
    ("Tripura", 27, "773.40"), ("Mizoram", 31, "586.45"),
    ("Sikkim", 14, "501.81"),
    # Andaman & Nicobar Islands row reads "10  10" in the document text
    # extraction -- reported count and amount are ambiguous (decimal cut off).
    # Excluded per the zero-guessing rule; logged below.
    ("Dadra & Nagar Haveli", 7, "99.02"), ("Daman and Diu", 1, "1.10"),
]
EXCLUDED.append((
    "Ambiguous cell excluded (not guessed)",
    "LS USQ 328 Annexure-III (2011-12): Andaman & Nicobar Islands row extracted "
    "as '10 10' -- reported count plausibly 10, amount truncated. Excluded.",
))

for _fy, _rows, _tot in [
    ("2009-10", _LS328_2009_10, ("22401", "1043522.09")),
    ("2010-11", _LS328_2010_11, ("22993", "1034358.43")),
    ("2011-12", _LS328_2011_12, ("21804", "1058195.61")),
]:
    for _st, _rep, _amt in _rows:
        STATE_ROWS.append({
            "state": _st, "financial_year": _fy, "metric": "received",
            "amount_str": _amt, "unit": "lakh",
            "reporting_associations": _rep, "source_id": "ls328",
            "table_ref": "Annexure-%s: Statewise FC received during %s"
                         % ({"2009-10": "I", "2010-11": "II",
                              "2011-12": "III"}[_fy], _fy),
            "notes": "2011-12 data flagged in source as 'some more data is "
                     "still under compilation'." if _fy == "2011-12" else "",
        })
    STATE_ROWS.append({
        "state": "ALL-INDIA", "financial_year": _fy, "metric": "received",
        "amount_str": _tot[1], "unit": "lakh",
        "reporting_associations": int(_tot[0]), "source_id": "ls328",
        "table_ref": "Answer table: Year / No. of NGOs / Total amount of "
                     "foreign contribution received (Rs in Lakhs)",
        "notes": "2011-12 total is provisional per source; stated total "
                 "includes the excluded Andaman & Nicobar row (implied "
                 "Rs 489.15 lakh by the document's own arithmetic)."
                 if _fy == "2011-12" else "",
    })

# ---- RS SQ 304 (24.3.2021) Annexure-I: state-wise FC received, exact Rupees --
_RS304_2016_17 = [
    ("Delhi", "36,07,91,92,896.65"), ("Tamil Nadu", "20,03,74,26,745.64"),
    ("Karnataka", "17,96,09,50,582.05"), ("Maharashtra", "17,21,32,77,651.57"),
    ("Andhra Pradesh", "9,11,51,25,022.64"), ("Kerala", "8,23,22,84,544.58"),
    ("West Bengal", "7,29,28,81,157.02"), ("Telangana", "7,17,07,01,723.59"),
    ("Gujarat", "5,58,06,27,582.75"), ("Rajasthan", "3,73,98,05,209.86"),
    ("Uttar Pradesh", "3,47,21,48,231.14"),
    ("Madhya Pradesh", "2,30,61,53,149.38"), ("Orissa", "2,15,87,47,671.90"),
    ("Bihar", "1,82,47,40,982.52"), ("Himachal Pradesh", "1,56,89,12,221.96"),
    ("Punjab", "1,41,28,58,268.25"), ("Uttarakhand", "1,35,04,65,899.78"),
    ("Jharkhand", "1,19,47,68,042.30"), ("Assam", "1,19,09,62,871.15"),
    ("Haryana", "84,04,92,621.46"), ("Meghalaya", "62,70,27,727.53"),
    ("Chhattisgarh", "54,80,21,347.65"),
    ("Jammu and Kashmir", "43,98,60,088.17"), ("Manipur", "38,83,78,093.58"),
    ("Nagaland", "34,19,06,272.60"), ("Pondicherry", "34,09,46,964.88"),
    ("Goa", "33,29,09,461.03"), ("Chandigarh", "23,69,82,483.44"),
    ("Mizoram", "20,47,39,815.87"), ("Arunachal Pradesh", "11,04,82,066.66"),
    ("Tripura", "10,81,81,328.11"), ("Sikkim", "9,23,42,844.53"),
    ("Andaman and Nicobar Islands", "3,02,52,021.04"),
    ("Dadra and Nagar Haveli", "71,88,271.00"),
]
_RS304_2017_18 = [
    ("Delhi", "44,62,80,76,025.48"), ("Tamil Nadu", "21,36,18,12,732.39"),
    ("Maharashtra", "18,26,12,43,182.69"), ("Karnataka", "16,13,19,19,595.96"),
    ("Kerala", "12,34,70,57,456.58"), ("Andhra Pradesh", "9,87,47,58,283.36"),
    ("Telangana", "8,62,58,77,244.28"), ("West Bengal", "6,94,60,44,693.12"),
    ("Gujarat", "6,90,43,38,818.86"), ("Uttar Pradesh", "3,51,28,83,590.62"),
    ("Orissa", "2,29,15,12,947.14"), ("Madhya Pradesh", "2,25,98,97,101.64"),
    ("Bihar", "2,07,54,26,626.54"), ("Himachal Pradesh", "1,81,80,07,063.09"),
    ("Rajasthan", "1,79,24,10,470.19"), ("Uttarakhand", "1,54,01,15,187.46"),
    ("Assam", "1,46,66,34,741.71"), ("Punjab", "1,41,14,96,300.28"),
    ("Haryana", "1,24,30,59,961.45"), ("Jharkhand", "1,16,23,84,663.23"),
    ("Meghalaya", "60,22,03,678.78"),
    ("Jammu and Kashmir", "55,76,20,323.95"), ("Chhattisgarh", "49,26,54,337.43"),
    ("Chandigarh", "43,49,33,420.01"), ("Manipur", "42,15,58,435.29"),
    ("Goa", "32,64,62,432.99"), ("Pondicherry", "29,52,91,275.78"),
    ("Nagaland", "26,57,90,279.70"), ("Arunachal Pradesh", "11,99,64,066.23"),
    ("Tripura", "9,67,70,937.98"), ("Sikkim", "7,00,43,491.52"),
    ("Mizoram", "3,08,63,119.30"),
    ("Andaman and Nicobar Islands", "2,56,04,554.74"),
    ("Dadra and Nagar Haveli", "1,10,33,492.56"),
]
_RS304_2018_19 = [
    ("Delhi", "43,70,44,75,053.67"), ("Tamil Nadu", "20,37,16,80,253.23"),
    ("Karnataka", "17,09,74,70,326.48"), ("Maharashtra", "17,06,53,95,977.49"),
    ("Kerala", "11,07,50,94,062.36"), ("Andhra Pradesh", "9,79,52,49,418.70"),
    ("Telangana", "7,45,30,11,418.86"), ("West Bengal", "7,12,49,32,884.04"),
    ("Gujarat", "6,68,05,40,584.46"), ("Uttar Pradesh", "3,97,11,45,081.96"),
    ("Orissa", "2,69,92,11,388.70"), ("Madhya Pradesh", "2,20,13,83,877.63"),
    ("Bihar", "2,05,48,71,036.01"), ("Himachal Pradesh", "1,97,21,17,122.52"),
    ("Rajasthan", "1,74,29,83,713.42"), ("Punjab", "1,54,44,89,448.85"),
    ("Assam", "1,38,76,25,654.47"), ("Uttarakhand", "1,29,80,64,903.65"),
    ("Jharkhand", "1,22,46,61,724.46"), ("Haryana", "78,50,36,168.91"),
    ("Meghalaya", "58,20,27,871.26"),
    ("Jammu and Kashmir", "51,74,75,126.95"), ("Nagaland", "44,23,17,234.39"),
    ("Chhattisgarh", "42,57,10,634.59"), ("Goa", "41,52,57,053.23"),
    ("Manipur", "39,76,39,260.56"), ("Pondicherry", "28,89,10,074.95"),
    ("Chandigarh", "28,60,86,327.83"), ("Tripura", "11,71,69,662.46"),
    ("Arunachal Pradesh", "6,90,28,829.22"), ("Sikkim", "6,37,24,379.00"),
    ("Mizoram", "3,14,84,031.67"), ("Dadra and Nagar Haveli", "1,15,04,912.50"),
    ("Andaman and Nicobar Islands", "1,11,22,802.00"),
]
_RS304_2019_20_PARTIAL = [
    ("Delhi", "4,20,46,73,104.45"), ("Kerala", "2,26,38,20,453.07"),
    ("West Bengal", "2,19,22,66,293.70"), ("Tamil Nadu", "2,18,17,28,945.81"),
    ("Karnataka", "1,27,68,86,961.72"), ("Telangana", "1,26,89,56,230.72"),
    ("Andhra Pradesh", "1,23,33,20,422.32"),
    ("Maharashtra", "1,13,03,86,583.02"), ("Gujarat", "89,13,83,581.72"),
    ("Punjab", "84,19,39,500.93"), ("Madhya Pradesh", "54,40,08,770.48"),
    ("Himachal Pradesh", "50,06,36,804.73"), ("Bihar", "49,11,92,070.97"),
    ("Orissa", "44,70,03,370.53"), ("Assam", "44,51,76,899.21"),
    ("Uttar Pradesh", "38,85,61,583.34"), ("Haryana", "37,37,56,139.75"),
    ("Rajasthan", "25,45,01,300.19"),
    ("Jammu and Kashmir", "20,50,89,204.12"), ("Jharkhand", "18,98,10,310.57"),
    ("Nagaland", "17,65,37,186.75"), ("Uttarakhand", "14,44,86,676.70"),
    ("Manipur", "5,66,08,183.73"), ("Chandigarh", "4,26,71,390.84"),
    ("Chhattisgarh", "4,06,49,759.29"), ("Meghalaya", "3,54,32,583.00"),
    ("Pondicherry", "3,12,76,682.52"), ("Tripura", "2,40,76,687.00"),
    ("Goa", "2,00,48,673.19"), ("Mizoram", "61,88,594.77"),
    ("Arunachal Pradesh", "18,56,304.26"),
    ("Andaman and Nicobar Islands", "1,67,919.00"), ("Sikkim", "1,63,706.00"),
]
_RS304_TOTALS = {
    "2016-17": ("18304", "1,53,55,17,41,862.28"),
    "2017-18": ("18235", "1,69,40,57,50,532.33"),
    "2018-19": ("17540", "1,64,90,88,98,300.48"),
    "2019-20": ("3475 (provisional)", "21,90,52,62,878.40"),
}
for _fy, _rows in [
    ("2016-17", _RS304_2016_17), ("2017-18", _RS304_2017_18),
    ("2018-19", _RS304_2018_19), ("2019-20", _RS304_2019_20_PARTIAL),
]:
    _partial = _fy == "2019-20"
    for _st, _amt in _rows:
        STATE_ROWS.append({
            "state": _st, "financial_year": _fy, "metric": "received",
            "amount_str": _amt, "unit": "rupee",
            "reporting_associations": None, "source_id": "rs304",
            "table_ref": "Annexure-I: Statement of State/UT-wise receipt of "
                         "foreign contribution (in Rupees) during %s" % _fy,
            "notes": "PARTIAL YEAR: only Annual Returns filed as on 16.03.2021; "
                     "filing deadline was extended to 30.06.2021." if _partial
                     else "",
        })
    _rep, _tot = _RS304_TOTALS[_fy]
    STATE_ROWS.append({
        "state": "ALL-INDIA", "financial_year": _fy, "metric": "received",
        "amount_str": _tot, "unit": "rupee",
        "reporting_associations": None, "source_id": "rs304",
        "table_ref": "Annexure-I total row",
        "notes": "Document states %s NGOs reported FC receipts in %s; "
                 "2019-20 provisional (ARs as on 16.03.2021)." % (_rep, _fy),
    })

# ---- LS USQ 457 (15.9.2020): national received totals, Rs in Crore ----
for _fy, _amt in [("2016-17", "18337.66"), ("2017-18", "19764.64"),
                  ("2018-19", "20011.21")]:
    STATE_ROWS.append({
        "state": "ALL-INDIA", "financial_year": _fy, "metric": "received",
        "amount_str": _amt, "unit": "crore",
        "reporting_associations": None, "source_id": "ls457",
        "table_ref": "Answer table: Year / Total FC received (Rs. in Crore)",
        "notes": "National figure only; 'Total FC utilized' column illegible "
                 "in text extraction -- excluded, not guessed.",
    })

# ---- RS USQ 3253 (29.3.2023): Rs in Crore; I=received, II=utilized ----
_RS3253_REC = {
    "2019-20": [("Andaman & Nicobar Islands", "2.52"),
                ("Andhra Pradesh", "1017.28"), ("Arunachal Pradesh", "12.57"),
                ("Assam", "162.48"), ("Bihar", "226.08"),
                ("Chandigarh", "39.19"), ("Chhattisgarh", "48.39"),
                ("Dadra & Nagar Haveli", "4.12"), ("Delhi", "4273.65"),
                ("Goa", "37.06"), ("Gujarat", "769.64"), ("Haryana", "82.09"),
                ("Himachal Pradesh", "228.77"), ("Jammu & Kashmir", "50.03"),
                ("Jharkhand", "130.72"), ("Karnataka", "1795.54"),
                ("Kerala", "868.01"), ("Madhya Pradesh", "220.06"),
                ("Maharashtra", "1567.28"), ("Manipur", "35.35"),
                ("Meghalaya", "59.64"), ("Mizoram", "2.63"),
                ("Nagaland", "48.94"), ("Orissa", "289.87"),
                ("Pondicherry", "27.37"), ("Punjab", "171.11"),
                ("Rajasthan", "158.61"), ("Sikkim", "9.04"),
                ("Tamil Nadu", "2162.66"), ("Telangana", "623.75"),
                ("Tripura", "10.74"), ("Uttar Pradesh", "373.01"),
                ("Uttarakhand", "124.08"), ("West Bengal", "727.20")],
    "2020-21": [("Andaman & Nicobar Islands", "3.68"),
                ("Andhra Pradesh", "954.57"), ("Arunachal Pradesh", "21.71"),
                ("Assam", "165.18"), ("Bihar", "217.37"),
                ("Chandigarh", "19.15"), ("Chhattisgarh", "52.13"),
                ("Dadra & Nagar Haveli", "2.43"), ("Delhi", "3979.52"),
                ("Goa", "46.36"), ("Gujarat", "908.00"), ("Haryana", "69.61"),
                ("Himachal Pradesh", "216.18"), ("Jammu & Kashmir", "56.05"),
                ("Jharkhand", "130.31"), ("Karnataka", "2304.80"),
                ("Kerala", "913.21"), ("Madhya Pradesh", "242.63"),
                ("Maharashtra", "1838.77"), ("Manipur", "50.97"),
                ("Meghalaya", "67.56"), ("Mizoram", "2.67"),
                ("Nagaland", "46.67"), ("Orissa", "249.98"),
                ("Pondicherry", "29.34"), ("Punjab", "140.83"),
                ("Rajasthan", "179.24"), ("Sikkim", "6.51"),
                ("Tamil Nadu", "2134.06"), ("Telangana", "815.45"),
                ("Tripura", "11.63"), ("Uttar Pradesh", "362.07"),
                ("Uttarakhand", "129.52"), ("West Bengal", "798.18")],
    "2021-22": [("Andaman & Nicobar Islands", "2.49"),
                ("Andhra Pradesh", "950.10"), ("Arunachal Pradesh", "27.50"),
                ("Assam", "199.64"), ("Bihar", "231.52"),
                ("Chandigarh", "20.08"), ("Chhattisgarh", "71.76"),
                ("Dadra & Nagar Haveli", "2.42"), ("Delhi", "5809.60"),
                ("Goa", "56.48"), ("Gujarat", "1496.17"), ("Haryana", "106.95"),
                ("Himachal Pradesh", "233.39"), ("Jammu & Kashmir", "55.77"),
                ("Jharkhand", "162.60"), ("Karnataka", "3140.98"),
                ("Kerala", "975.44"), ("Madhya Pradesh", "268.31"),
                ("Maharashtra", "2199.96"), ("Manipur", "60.08"),
                ("Meghalaya", "78.35"), ("Mizoram", "15.05"),
                ("Nagaland", "57.18"), ("Orissa", "288.02"),
                ("Pondicherry", "25.63"), ("Punjab", "207.29"),
                ("Rajasthan", "285.09"), ("Sikkim", "7.46"),
                ("Tamil Nadu", "2507.35"), ("Telangana", "1114.55"),
                ("Tripura", "12.37"), ("Uttar Pradesh", "375.81"),
                ("Uttarakhand", "170.24"), ("West Bengal", "906.12")],
}
_RS3253_UTIL = {
    "2019-20": [("Andaman & Nicobar Islands", "3.71"),
                ("Andhra Pradesh", "1249.24"), ("Arunachal Pradesh", "14.44"),
                ("Assam", "182.24"), ("Bihar", "560.00"),
                ("Chandigarh", "50.17"), ("Chhattisgarh", "79.81"),
                ("Dadra & Nagar Haveli", "3.74"), ("Delhi", "7440.55"),
                ("Goa", "40.85"), ("Gujarat", "2860.05"), ("Haryana", "84.14"),
                ("Himachal Pradesh", "297.58"), ("Jammu & Kashmir", "53.97"),
                ("Jharkhand", "187.48"), ("Karnataka", "2386.56"),
                ("Kerala", "262.99"), ("Madhya Pradesh", "357.01"),
                ("Maharashtra", "3297.08"), ("Manipur", "45.59"),
                ("Meghalaya", "58.61"), ("Mizoram", "6.69"),
                ("Nagaland", "54.75"), ("Orissa", "1628.77"),
                ("Pondicherry", "33.60"), ("Punjab", "212.21"),
                ("Rajasthan", "1045.91"), ("Sikkim", "7.72"),
                ("Tamil Nadu", "2602.66"), ("Telangana", "865.47"),
                ("Tripura", "10.95"), ("Uttar Pradesh", "551.78"),
                ("Uttarakhand", "219.06"), ("West Bengal", "1229.48")],
    "2020-21": [("Andaman & Nicobar Islands", "4.33"),
                ("Andhra Pradesh", "1362.27"), ("Arunachal Pradesh", "23.12"),
                ("Assam", "203.17"), ("Bihar", "282.49"),
                ("Chandigarh", "16.03"), ("Chhattisgarh", "105.00"),
                ("Dadra & Nagar Haveli", "5.19"), ("Delhi", "4400.52"),
                ("Goa", "49.10"), ("Gujarat", "873.60"), ("Haryana", "87.45"),
                ("Himachal Pradesh", "231.10"), ("Jammu & Kashmir", "51.03"),
                ("Jharkhand", "201.43"), ("Karnataka", "2344.91"),
                ("Kerala", "221.77"), ("Madhya Pradesh", "373.97"),
                ("Maharashtra", "2217.94"), ("Manipur", "54.31"),
                ("Meghalaya", "113.12"), ("Mizoram", "4.18"),
                ("Nagaland", "47.41"), ("Orissa", "285.04"),
                ("Pondicherry", "37.92"), ("Punjab", "179.99"),
                ("Rajasthan", "1253.16"), ("Sikkim", "7.25"),
                ("Tamil Nadu", "7266.46"), ("Telangana", "1160.78"),
                ("Tripura", "14.27"), ("Uttar Pradesh", "623.30"),
                ("Uttarakhand", "147.06"), ("West Bengal", "1437.68")],
    "2021-22": [("Andaman & Nicobar Islands", "4.11"),
                ("Andhra Pradesh", "1049.00"), ("Arunachal Pradesh", "23.51"),
                ("Assam", "215.22"), ("Bihar", "278.98"),
                ("Chandigarh", "21.26"), ("Chhattisgarh", "86.13"),
                ("Dadra & Nagar Haveli", "1.52"), ("Delhi", "6008.73"),
                ("Goa", "55.53"), ("Gujarat", "1671.59"), ("Haryana", "107.35"),
                ("Himachal Pradesh", "247.21"), ("Jammu & Kashmir", "55.68"),
                ("Jharkhand", "471.83"), ("Karnataka", "4227.99"),
                ("Kerala", "396.03"), ("Madhya Pradesh", "360.06"),
                ("Maharashtra", "2536.21"), ("Manipur", "58.09"),
                ("Meghalaya", "83.14"), ("Mizoram", "14.57"),
                ("Nagaland", "62.91"), ("Orissa", "340.80"),
                ("Pondicherry", "30.45"), ("Punjab", "205.64"),
                ("Rajasthan", "1035.61"), ("Sikkim", "8.27"),
                ("Tamil Nadu", "2647.39"), ("Telangana", "1214.77"),
                ("Tripura", "18.77"), ("Uttar Pradesh", "504.42"),
                ("Uttarakhand", "170.46"), ("West Bengal", "1293.64")],
}
for _fy in ("2019-20", "2020-21", "2021-22"):
    for _st, _amt in _RS3253_REC[_fy]:
        STATE_ROWS.append({
            "state": _st, "financial_year": _fy, "metric": "received",
            "amount_str": _amt, "unit": "crore",
            "reporting_associations": None, "source_id": "rs3253",
            "table_ref": "Annexure-I: Statewise Receipt of foreign "
                         "contribution during %s (Rs in Crore)" % _fy,
            "notes": "Based on Annual Returns submitted as on 22.03.2023.",
        })
    for _st, _amt in _RS3253_UTIL[_fy]:
        STATE_ROWS.append({
            "state": _st, "financial_year": _fy, "metric": "utilized",
            "amount_str": _amt, "unit": "crore",
            "reporting_associations": None, "source_id": "rs3253",
            "table_ref": "Annexure-II: Statewise Utilisation of foreign "
                         "contribution during %s (Rs in Crore)" % _fy,
            "notes": "Utilized can exceed received: it includes opening "
                     "balances / prior-year funds per FC-4 annual returns.",
        })

# ---- RS USQ 3253 Annexure-III: cancellations, 2020 to 22.03.2023 ----
CANCELLATION_ROWS = [
    ("Andhra Pradesh", 168), ("Arunachal Pradesh", 2),
    ("Assam", 23), ("Bihar", 122), ("Chhattisgarh", 4),
    ("Delhi", 14), ("Goa", 73), ("Gujarat", 4),
    ("Haryana", 45), ("Himachal Pradesh", 9), ("Jharkhand", 8),
    ("Karnataka", 10), ("Kerala", 43), ("Madhya Pradesh", 101),
    ("Maharashtra", 52), ("Manipur", 54), ("Meghalaya", 207),
    ("Mizoram", 43), ("Nagaland", 7), ("Odisha", 2),
    ("Puducherry", 14), ("Punjab", 111), ("Rajasthan", 8),
    ("Sikkim", 8), ("Tamil Nadu", 41), ("Telangana", 3),
    ("Tripura", 219), ("Uttar Pradesh", 90), ("Uttarakhand", 3),
    ("West Bengal", 116), ("Jammu & Kashmir", 31), ("Ladakh", 193),
]

# ---- BusinessLine / MHA JPC briefing (19.9.2026): Rs in Crore ----
# State-level 2024-25 receipts named in the article:
for _st, _amt in [("Delhi", "5834"), ("Karnataka", "3164"),
                  ("Maharashtra", "2385"), ("Tamil Nadu", "2313")]:
    STATE_ROWS.append({
        "state": _st, "financial_year": "2024-25", "metric": "received",
        "amount_str": _amt, "unit": "crore",
        "reporting_associations": None, "source_id": "bl_jpc",
        "table_ref": "Article text: 'Rs 5,834 crore in Delhi, Rs 3,164 crore "
                     "in Karnataka, Rs 2,385 crore in Maharashtra and "
                     "Rs 2,313 crore in Tamil Nadu'",
        "notes": "Secondary reporting of an MHA briefing to the JPC; not an "
                 "official published table.",
    })
# State-wise ACTIVE FCRA NGO counts (registered under FCRA), 2024-25 briefing:
_BL_NGO_COUNTS = [("Tamil Nadu", 2102), ("Maharashtra", 1578),
                  ("Karnataka", 1355), ("Delhi", 1218),
                  ("Andhra Pradesh", 1022), ("Kerala", 1013)]
for _st, _n in _BL_NGO_COUNTS:
    STATE_ROWS.append({
        "state": _st, "financial_year": "2024-25", "metric": "active_ngos",
        "amount_str": "", "unit": "",
        "reporting_associations": _n, "source_id": "bl_jpc",
        "table_ref": "Article text: state-wise active FCRA-registered NGOs",
        "notes": "Count of active FCRA-registered NGOs, not a receipt figure.",
    })
# National contextual rows (2015-16 and 2024-25), kept per-source:
for _fy, _amt, _n, _note in [
    ("2015-16", "17832", 29022, "MHA: 29,022 active FCRA NGOs in 2015."),
    ("2024-25", "22974", 14466,
     "MHA JPC briefing: 14,466 'FCRA registered active NGOs across 15 "
     "states'; total FC received Rs 22,974 crore."),
]:
    STATE_ROWS.append({
        "state": "ALL-INDIA", "financial_year": _fy, "metric": "received",
        "amount_str": _amt, "unit": "crore",
        "reporting_associations": None, "source_id": "bl_jpc",
        "table_ref": "Article text",
        "notes": "Secondary reporting of MHA briefing. " + _note,
    })
    STATE_ROWS.append({
        "state": "ALL-INDIA", "financial_year": _fy, "metric": "active_ngos",
        "amount_str": "", "unit": "",
        "reporting_associations": _n, "source_id": "bl_jpc",
        "table_ref": "Article text",
        "notes": "Secondary reporting of MHA briefing. " + _note,
    })

# ---- PIB backgrounder (22.7.2026): national 2024-25, Rs in Crore ----
STATE_ROWS.append({
    "state": "ALL-INDIA", "financial_year": "2024-25", "metric": "received",
    "amount_str": "22963", "unit": "crore",
    "reporting_associations": 16200, "source_id": "pib_fcra",
    "table_ref": "Backgrounder: 'Around 16,200 actively registered "
                 "associations received around Rs 22,963 crore ... in "
                 "2024-25'",
    "notes": "Official PIB figure. Differs slightly from BusinessLine's "
             "Rs 22,974 crore (MHA JPC briefing) -- kept as separate "
             "per-source rows, not reconciled.",
})

# ----------------------------------------------------------------------------
# DONOR-COUNTRY ROWS (country, financial_year, amount_str, unit, notes)
# RS SQ 304 Annexure-II: "Country of Donors Foreign Contribution (in Rupees)".
# Excludes donor details < Rs 20,000 as declared in statutory Form FC-4.
# ----------------------------------------------------------------------------
DONOR_ROWS = []

_RS304_DONORS = {
    "2016-17": [
        ("United States of America", "58,69,31,51,335.53"),
        ("India", "24,86,18,72,939.04"),
        ("United Kingdom", "14,78,42,85,251.25"),
        ("Germany", "12,93,99,02,689.87"),
        ("Switzerland", "4,81,46,22,000.89"),
        ("Italy", "4,60,35,43,601.09"),
        ("Spain", "3,75,88,92,093.78"),
        ("Netherlands", "3,73,46,39,702.86"),
        ("Canada", "3,73,40,78,109.03"),
        ("United Arab Emirates", "2,13,89,69,238.90"),
        ("Australia", "2,11,78,04,468.60"),
        ("France", "1,92,69,91,255.05"),
        ("Austria", "1,37,17,35,859.76"),
        ("Belgium", "1,02,05,99,654.43"),
        ("Hong Kong", "93,11,25,850.46"),
        ("Sweden", "88,53,34,225.13"),
        ("Singapore", "85,35,08,976.39"),
        ("Kuwait", "73,36,40,123.84"),
        ("Norway", "61,75,23,002.35"),
        ("Japan", "54,61,70,240.58"),
        ("Liechtenstein", "48,49,40,552.64"),
        ("Ireland", "45,38,81,941.27"),
        ("Qatar", "43,38,55,158.49"),
        ("New Zealand", "39,13,01,106.09"),
        ("Denmark", "37,55,84,264.65"),
        ("Philippines", "29,39,83,817.76"),
        ("South Korea", "28,76,75,183.55"),
        ("Taiwan", "27,47,62,679.73"),
        ("Finland", "24,87,20,343.37"),
        ("South Africa", "22,92,33,378.06"),
        ("Luxembourg", "19,37,70,196.48"),
        ("Swaziland", "16,77,65,523.53"),
        ("Malaysia", "13,90,23,383.40"),
        ("Czech Republic", "11,89,80,182.85"),
        ("Thailand", "11,00,71,545.90"),
        ("Indonesia", "10,30,48,287.85"),
        ("Nepal", "9,71,98,957.34"),
        ("Saudi Arabia", "9,57,91,069.10"),
        ("Panama", "7,65,71,449.63"),
        ("Morocco", "7,06,80,991.12"),
        ("Monaco", "6,85,19,867.69"),
        ("Mauritius", "6,64,47,624.20"),
        ("China", "5,86,44,605.78"),
        ("Turkey", "5,74,61,810.91"),
        ("Sri Lanka", "4,69,03,871.25"),
        ("Oman", "4,44,67,587.53"),
        ("Bahamas", "4,41,21,237.90"),
        ("Kenya", "4,02,52,750.29"),
        ("Bangladesh", "3,64,52,782.32"),
        ("Nigeria", "3,63,87,914.60"),
        ("Egypt", "3,12,48,357.36"),
        ("Malta", "2,94,07,346.09"),
        ("Iceland", "2,93,65,071.33"),
        ("Israel", "2,78,37,439.75"),
        ("Cayman Islands", "2,53,77,151.88"),
        ("Slovakia", "2,45,65,449.32"),
        ("Poland", "2,37,82,420.55"),
        ("Greece", "2,20,23,310.53"),
        ("Azerbaijan", "1,98,47,433.36"),
        ("Afghanistan", "1,97,33,602.53"),
        ("Tanzania", "1,90,52,736.90"),
        ("Seychelles", "1,86,91,803.00"),
        ("Jamaica", "1,71,57,927.00"),
        ("Chile", "1,69,37,152.06"),
        ("Reunion Island", "1,57,17,810.68"),
        ("Vatican City", "1,54,02,046.17"),
        ("Brazil", "1,50,71,933.33"),
        ("Georgia", "1,45,09,142.11"),
        ("Bulgaria", "1,33,02,245.80"),
        ("Armenia", "1,09,05,753.00"),
        ("Ethiopia", "1,07,26,967.00"),
        ("Bahrain", "1,06,36,249.30"),
        ("Mexico", "1,03,90,145.55"),
        ("Bhutan", "1,00,95,153.01"),
        ("Columbia", "95,38,606.33"),
        ("Russia", "85,07,202.77"),
        ("Romania", "84,99,996.43"),
        ("Barbados", "83,73,040.00"),
        ("Netherlands Antilles", "76,12,149.00"),
        ("Uganda", "69,25,788.56"),
        ("Argentina", "64,84,714.00"),
        ("Portugal", "63,39,298.89"),
        ("Slovenia", "56,04,576.96"),
        ("Trinidad and Tobago", "51,73,842.72"),
        ("Botswana", "43,74,655.00"),
        ("Zambia", "41,16,006.00"),
        ("Hungary", "36,26,049.24"),
        ("Pakistan", "35,70,380.91"),
        ("Central African Republic", "34,96,210.86"),
        ("Iran", "28,86,279.50"),
        ("Vietnam", "27,96,120.30"),
        ("Cambodia", "25,76,397.57"),
        ("Mongolia", "24,93,617.00"),
        ("Others (Tibet)", "23,15,609.78"),
        ("Croatia", "21,26,527.44"),
        ("Ghana", "21,13,480.00"),
        ("Guyana", "20,23,207.30"),
        ("Jordan", "18,93,649.59"),
        ("Peru", "16,14,521.90"),
        ("Bosnia", "14,43,885.00"),
        ("Mali", "14,02,450.00"),
        ("Lebanon", "11,39,255.00"),
        ("Tunisia", "11,01,093.00"),
        ("Myanmar", "10,38,923.00"),
        ("Malawi", "10,22,368.00"),
        ("Dominica", "8,91,994.61"),
        ("Fiji", "8,66,209.10"),
        ("Sudan", "7,50,072.00"),
        ("Estonia", "7,16,500.00"),
        ("Maldives", "6,90,483.00"),
        ("Papua New Guinea", "6,78,077.00"),
        ("Congo", "6,27,812.00"),
        ("New Caledonia", "6,05,231.00"),
        ("Ukraine", "5,21,523.32"),
        ("Liberia", "5,20,520.00"),
        ("Uruguay", "4,84,392.00"),
        ("Tajikistan", "4,09,335.00"),
        ("Mongolia (Peoples Rep)", "3,68,473.20"),
        ("Mozambique", "3,35,101.00"),
        ("Zimbabwe", "3,30,355.00"),
        ("St. Christopher and Nevis", "2,63,783.00"),
        ("Malagasy (Madagascar)", "1,53,410.00"),
        ("Gambia", "1,33,915.00"),
        ("Belarus", "1,25,047.00"),
        ("Lithuania", "1,17,913.00"),
        ("Costa Rica", "89,772.06"),
        ("Serbia", "71,628.00"),
        ("Brunei", "70,367.00"),
        ("Laos", "65,950.00"),
        ("Rwanda", "49,000.00"),
        ("Kyrgyzstan", "48,000.00"),
        ("Venezuela", "26,446.00"),
    ],
    "2017-18": [
        ("United States of America", "61,99,10,83,664.03"),
        ("India", "23,23,93,18,853.21"),
        ("United Kingdom", "14,86,40,69,866.28"),
        ("Germany", "14,61,88,78,664.48"),
        ("Netherlands", "11,81,46,20,103.73"),
        ("South Korea", "5,10,45,93,646.67"),
        ("Switzerland", "4,89,86,94,610.67"),
        ("Italy", "4,52,34,75,998.91"),
        ("Canada", "4,27,34,67,104.42"),
        ("Spain", "3,96,30,37,594.86"),
        ("Australia", "2,43,37,50,426.12"),
        ("France", "2,14,93,92,170.70"),
        ("Austria", "1,47,24,53,811.05"),
        ("Hong Kong", "1,19,90,13,733.35"),
        ("Sweden", "1,14,51,68,874.19"),
        ("United Arab Emirates", "1,07,66,13,056.88"),
        ("Belgium", "96,09,81,166.60"),
        ("Kuwait", "80,49,33,029.19"),
        ("South Africa", "61,30,08,693.66"),
        ("Norway", "60,21,15,262.81"),
        ("Singapore", "55,87,82,898.92"),
        ("Japan", "51,20,08,578.08"),
        ("Ireland", "41,62,50,074.99"),
        ("Taiwan", "37,95,89,923.34"),
        ("Denmark", "32,96,73,357.30"),
        ("Qatar", "31,10,09,928.00"),
        ("New Zealand", "28,99,26,258.69"),
        ("Finland", "26,98,99,095.12"),
        ("Thailand", "26,36,40,712.08"),
        ("Philippines", "23,58,88,158.16"),
        ("Swaziland", "21,45,08,850.01"),
        ("Luxembourg", "16,71,00,800.28"),
        ("Czech Republic", "13,56,89,837.08"),
        ("Malaysia", "13,32,68,400.44"),
        ("Nepal", "10,53,85,312.09"),
        ("China", "9,25,91,931.50"),
        ("Liechtenstein", "9,08,21,052.25"),
        ("Bahamas", "7,60,54,220.00"),
        ("Indonesia", "6,47,12,324.49"),
        ("Oman", "6,22,60,624.89"),
        ("Turkey", "6,08,45,447.81"),
        ("Kenya", "5,06,21,597.04"),
        ("Morocco", "4,98,61,796.94"),
        ("Monaco", "4,88,74,149.74"),
        ("Sri Lanka", "4,67,33,707.50"),
        ("Saudi Arabia", "3,99,12,271.60"),
        ("Vatican City", "3,86,64,011.00"),
        ("Poland", "2,85,90,764.99"),
        ("Israel", "2,73,01,186.49"),
        ("Others (Tibet)", "2,69,65,736.00"),
        ("Malta", "2,30,43,772.48"),
        ("Peru", "2,21,95,053.00"),
        ("Slovakia", "2,21,12,974.46"),
        ("Panama", "2,06,58,034.00"),
        ("Iceland", "2,00,89,796.42"),
        ("Belize", "1,94,32,740.00"),
        ("Azerbaijan", "1,75,58,017.39"),
        ("Bangladesh", "1,73,92,552.00"),
        ("Jamaica", "1,69,83,457.00"),
        ("Seychelles", "1,69,61,344.00"),
        ("Mauritius", "1,51,95,396.00"),
        ("Mongolia", "1,47,18,606.00"),
        ("Mexico", "1,45,08,751.00"),
        ("Bhutan", "1,43,66,659.82"),
        ("Bahrain", "1,28,72,106.00"),
        ("Tanzania", "1,19,95,776.03"),
        ("Columbia", "1,15,18,231.00"),
        ("Bosnia", "1,10,63,185.00"),
        ("Myanmar", "1,05,97,665.00"),
        ("Slovenia", "1,05,29,339.66"),
        ("Georgia", "99,56,299.00"),
        ("Botswana", "92,40,286.00"),
        ("Hungary", "92,15,101.82"),
        ("Chile", "88,27,692.00"),
        ("Cayman Islands", "78,21,477.33"),
        ("Portugal", "76,48,680.96"),
        ("Greece", "74,19,134.00"),
        ("Brazil", "73,59,996.55"),
        ("Argentina", "70,30,298.00"),
        ("Barbados", "68,14,557.48"),
        ("Romania", "67,90,077.27"),
        ("Central African Republic", "67,24,360.00"),
        ("Reunion Island", "66,11,356.40"),
        ("Netherlands Antilles", "66,03,123.00"),
        ("Armenia", "61,30,317.00"),
        ("Uganda", "59,59,694.00"),
        ("Gambia", "56,80,786.00"),
        ("Afghanistan", "46,40,779.52"),
        ("Croatia", "45,45,628.76"),
        ("Dominican Republic", "37,84,181.00"),
        ("Albania", "34,57,366.00"),
        ("Cambodia", "33,88,091.44"),
        ("Congo", "33,25,397.42"),
        ("Russia", "30,26,604.95"),
        ("Nigeria", "29,99,191.00"),
        ("Gabon", "29,98,552.00"),
        ("Pakistan", "29,21,748.44"),
        ("Trinidad and Tobago", "28,25,415.96"),
        ("Mongolia (Peoples Rep)", "19,31,296.18"),
        ("Fiji", "19,24,412.00"),
        ("St. Vincent and the Grenadines", "19,19,089.00"),
        ("Herzegovina", "18,64,250.00"),
        ("Costa Rica", "16,37,618.26"),
        ("Bulgaria", "16,26,030.50"),
        ("Cuba", "15,80,895.37"),
        ("Suriname", "15,60,000.00"),
        ("Rwanda", "15,16,579.00"),
        ("Nicaragua", "14,90,064.00"),
        ("Liberia", "14,53,506.50"),
        ("Zambia", "13,43,575.00"),
        ("Vietnam", "12,88,286.54"),
        ("Lithuania", "12,48,460.00"),
        ("Macau", "11,68,815.00"),
        ("St. Christopher and Nevis", "10,05,366.00"),
        ("Maldives", "8,76,976.00"),
        ("Guinea", "8,25,090.00"),
        ("Lebanon", "8,09,389.00"),
        ("Egypt", "7,95,592.00"),
        ("Guyana", "7,56,055.00"),
        ("Tajikistan", "7,48,835.00"),
        ("Papua New Guinea", "7,29,377.00"),
        ("New Caledonia", "7,24,187.00"),
        ("Cape Verde Islands", "6,84,751.00"),
        ("Ethiopia", "6,70,554.00"),
        ("Jordan", "6,32,174.00"),
        ("Sudan", "6,31,368.00"),
        ("Uruguay", "6,10,258.50"),
        ("Zimbabwe", "5,01,332.00"),
        ("Senegal", "3,45,443.00"),
        ("Paraguay", "2,88,483.00"),
        ("Ghana", "2,34,542.00"),
        ("Cyprus", "1,94,444.00"),
        ("Laos", "1,90,665.00"),
        ("Sierra Leone", "1,47,363.00"),
        ("Serbia", "1,26,767.00"),
        ("Cardine Mashal Islands", "1,14,569.00"),
        ("Malagasy (Madagascar)", "99,827.00"),
        ("Latvia", "98,420.00"),
        ("Iran", "95,415.00"),
        ("Estonia", "83,478.00"),
        ("Aruba", "78,143.00"),
        ("Guatemala", "37,500.00"),
        ("Iraq", "35,312.00"),
        ("Libya", "31,920.00"),
        ("North Korea", "31,000.00"),
        ("Syria", "29,688.00"),
    ],
}
_RS304_DONORS["2018-19"] = [
    ("United States of America", "69,07,32,53,246.28"),
    ("India", "23,26,20,93,103.07"),
    ("United Kingdom", "16,66,27,14,150.04"),
    ("Germany", "15,65,05,17,518.07"),
    ("Switzerland", "5,78,70,34,884.34"),
    ("Italy", "4,96,01,17,980.88"),
    ("Netherlands", "4,46,72,07,866.04"),
    ("Canada", "4,21,01,81,389.85"),
    ("Spain", "4,19,36,75,003.66"),
    ("Mauritius", "3,76,39,95,220.39"),
    ("Australia", "2,48,97,30,564.46"),
    ("United Arab Emirates", "2,33,40,13,157.61"),
    ("France", "2,05,53,10,793.38"),
    ("Austria", "1,55,15,17,381.59"),
    ("Hong Kong", "1,31,04,49,354.87"),
    ("Kuwait", "1,23,67,16,762.19"),
    ("Sweden", "1,23,41,35,003.49"),
    ("Belgium", "95,40,94,029.52"),
    ("Singapore", "78,29,18,594.35"),
    ("Japan", "74,64,28,836.45"),
    ("Norway", "69,89,28,047.20"),
    ("South Africa", "49,85,68,426.89"),
    ("Qatar", "45,55,57,511.04"),
    ("Ireland", "42,14,24,986.87"),
    ("New Zealand", "40,20,00,717.85"),
    ("Taiwan", "40,13,64,260.29"),
    ("Saudi Arabia", "39,57,97,403.08"),
    ("Denmark", "37,29,14,000.58"),
    ("Finland", "27,13,04,585.67"),
    ("South Korea", "26,55,57,774.82"),
    ("Philippines", "22,39,69,394.10"),
    ("Swaziland", "21,56,60,917.32"),
    ("Malaysia", "21,50,71,831.20"),
    ("Luxembourg", "21,06,08,041.09"),
    ("Thailand", "19,93,31,260.13"),
    ("Czech Republic", "16,20,98,790.05"),
    ("Bahamas", "15,38,63,430.00"),
    ("Liechtenstein", "13,79,43,428.96"),
    ("Nepal", "13,44,76,387.80"),
    ("China", "11,76,75,698.04"),
    ("Iceland", "9,71,42,435.14"),
    ("Indonesia", "8,82,93,714.99"),
    ("Panama", "8,43,65,007.00"),
    ("Turkey", "8,40,95,125.50"),
    ("Sri Lanka", "8,14,83,139.20"),
    ("Oman", "7,84,52,455.87"),
    ("Vatican City", "6,21,95,482.50"),
    ("Kenya", "6,15,45,031.66"),
    ("Vietnam", "5,28,90,053.51"),
    ("Monaco", "4,38,84,378.26"),
    ("Slovakia", "3,92,56,547.86"),
    ("Poland", "3,05,13,069.65"),
    ("Tanzania", "3,03,60,243.14"),
    ("Malta", "2,95,76,499.01"),
    ("Others (Tibet)", "2,71,21,794.52"),
    ("Hungary", "2,57,58,672.27"),
    ("Chile", "2,24,64,436.57"),
    ("Morocco", "2,06,50,397.88"),
    ("Jamaica", "2,05,73,468.00"),
    ("Portugal", "1,77,48,283.34"),
    ("Afghanistan", "1,74,33,452.58"),
    ("Slovenia", "1,59,61,437.01"),
    ("Bahrain", "1,41,81,489.86"),
    ("Netherlands Antilles", "1,31,16,217.00"),
    ("Mexico", "1,29,06,412.63"),
    ("Georgia", "1,26,65,342.60"),
    ("Liberia", "1,07,55,049.00"),
    ("Lebanon", "1,07,12,018.50"),
    ("Uganda", "1,04,45,266.78"),
    ("Romania", "1,03,63,047.93"),
    ("Bangladesh", "1,00,79,811.00"),
    ("Greece", "90,49,457.21"),
    ("Columbia", "87,50,817.46"),
    ("Israel", "86,46,891.80"),
    ("Trinidad and Tobago", "85,18,701.32"),
    ("Bhutan", "77,28,673.03"),
    ("Nigeria", "70,28,930.62"),
    ("Seychelles", "69,10,070.00"),
    ("Bosnia", "69,04,580.00"),
    ("Cyprus", "68,48,816.00"),
    ("Barbados", "63,15,239.18"),
    ("Botswana", "62,74,702.00"),
    ("Peru", "57,62,779.86"),
    ("Sudan", "53,26,583.00"),
    ("Lithuania", "52,15,223.90"),
    ("Reunion Island", "37,33,104.00"),
    ("Costa Rica", "33,73,691.71"),
    ("Gabon", "32,99,426.00"),
    ("Dominican Republic", "30,86,784.00"),
    ("Bulgaria", "30,76,669.00"),
    ("Brazil", "29,86,070.58"),
    ("Croatia", "29,46,946.03"),
    ("St. Vincent and the Grenadines", "29,24,671.00"),
    ("Cayman Islands", "25,08,731.00"),
    ("North Korea", "23,41,901.00"),
    ("Cambodia", "22,47,047.39"),
    ("Ghana", "22,26,372.00"),
    ("Cape Verde Islands", "21,40,314.00"),
    ("Mongolia", "20,60,696.75"),
    ("Armenia", "20,30,401.33"),
    ("Guyana", "19,88,111.00"),
    ("Pakistan", "19,16,368.00"),
    ("Cuba", "17,16,530.82"),
    ("Mali", "16,03,800.00"),
    ("Papua New Guinea", "15,89,822.00"),
    ("Maldives", "14,93,061.20"),
    ("Ukraine", "14,23,201.11"),
    ("Uruguay", "14,10,386.08"),
    ("Albania", "12,59,645.00"),
    ("Cameroon", "10,52,573.90"),
    ("Mongolia (Peoples Rep)", "9,58,986.37"),
    ("Latvia", "9,15,173.50"),
    ("Russia", "7,77,567.90"),
    ("Argentina", "7,71,117.32"),
    ("Central African Republic", "6,51,688.00"),
    ("Solomon Islands", "6,10,301.00"),
    ("Estonia", "5,88,904.51"),
    ("Namibia", "4,66,890.00"),
    ("Fiji", "4,19,807.00"),
    ("St. Christopher and Nevis", "4,12,789.00"),
    ("Macedonia", "4,03,195.00"),
    ("Senegal", "3,99,503.00"),
    ("Nicaragua", "3,84,803.00"),
    ("Myanmar", "3,79,812.50"),
    ("Kazakhstan", "2,86,963.00"),
    ("Laos", "2,32,150.00"),
    ("Iran", "2,13,151.86"),
    ("Jordan", "94,355.46"),
    ("Ethiopia", "92,652.00"),
    ("Serbia", "91,828.25"),
    ("Mozambique", "68,633.00"),
    ("Malagasy (Madagascar)", "35,122.55"),
    ("Rwanda", "33,650.00"),
    ("Guinea", "29,410.00"),
    ("Lesotho", "19,700.00"),
    ("Zimbabwe", "16,000.00"),
]

_RS304_DONORS["2019-20-partial"] = [
    ("United States of America", "9,66,47,27,390.68"),
    ("India", "3,19,49,47,224.47"),
    ("United Kingdom", "2,85,57,94,815.73"),
    ("Germany", "2,34,08,31,119.27"),
    ("Italy", "73,09,83,200.48"),
    ("Switzerland", "66,82,57,086.64"),
    ("Netherlands", "66,31,21,878.19"),
    ("Canada", "44,29,17,957.26"),
    ("Australia", "36,68,66,980.65"),
    ("France", "30,28,82,880.18"),
    ("Belgium", "24,93,20,104.89"),
    ("Sweden", "24,89,01,886.60"),
    ("Hong Kong", "21,17,66,063.42"),
    ("Kuwait", "20,71,27,124.17"),
    ("Austria", "20,61,43,927.11"),
    ("Spain", "20,08,06,230.20"),
    ("Singapore", "8,92,42,591.80"),
    ("Denmark", "8,79,44,655.31"),
    ("New Zealand", "7,36,55,682.53"),
    ("Norway", "7,36,17,543.22"),
    ("Thailand", "6,74,64,417.10"),
    ("Japan", "5,82,63,115.02"),
    ("Panama", "5,36,94,212.00"),
    ("Luxembourg", "4,41,65,037.98"),
    ("Swaziland", "4,15,31,474.00"),
    ("United Arab Emirates", "3,91,09,875.95"),
    ("Taiwan", "3,83,61,367.38"),
    ("Ireland", "3,74,81,002.30"),
    ("Finland", "2,70,34,273.25"),
    ("Malaysia", "2,46,27,472.84"),
    ("Philippines", "2,15,19,743.30"),
    ("Hungary", "1,63,96,428.00"),
    ("Suriname", "1,32,54,294.00"),
    ("Czech Republic", "1,15,15,950.10"),
    ("South Africa", "80,36,296.98"),
    ("Portugal", "62,27,839.64"),
    ("Turkey", "61,99,243.00"),
    ("Bangladesh", "60,03,580.00"),
    ("Chile", "57,00,763.00"),
    ("Iceland", "51,77,636.00"),
    ("South Korea", "50,73,323.00"),
    ("Kenya", "47,50,995.00"),
    ("Malta", "46,72,560.76"),
    ("Afghanistan", "38,65,464.00"),
    ("Nepal", "34,38,488.23"),
    ("Mongolia", "30,19,109.00"),
    ("Egypt", "23,94,127.28"),
    ("Sri Lanka", "23,20,878.00"),
    ("Saudi Arabia", "23,07,050.00"),
    ("Poland", "18,55,657.20"),
    ("Zambia", "15,30,077.56"),
    ("Tanzania", "14,99,975.00"),
    ("Mexico", "14,15,160.00"),
    ("Mauritius", "13,57,615.00"),
    ("Brazil", "12,99,793.00"),
    ("Uruguay", "10,94,133.36"),
    ("Greece", "10,42,652.00"),
    ("Uganda", "9,33,896.00"),
    ("Liechtenstein", "7,66,320.00"),
    ("Bhutan", "6,42,116.00"),
    ("New Caledonia", "6,07,769.00"),
    ("Somalia", "5,12,026.00"),
    ("Indonesia", "4,56,381.00"),
    ("Monaco", "4,00,250.00"),
    ("Reunion Island", "3,94,450.00"),
    ("Oman", "3,84,546.92"),
    ("Bahrain", "3,30,000.00"),
    ("Armenia", "3,09,500.00"),
    ("Barbados", "2,77,100.00"),
    ("Trinidad and Tobago", "2,64,742.00"),
    ("China", "2,64,146.00"),
    ("Myanmar", "2,44,055.00"),
    ("Vietnam", "1,54,002.00"),
    ("Slovenia", "76,484.50"),
    ("Slovakia", "45,097.65"),
    ("Russia", "31,795.00"),
]

_RS304_DONOR_TOTALS = {
    "2016-17": "1,50,79,89,16,543.06",
    "2017-18": "1,67,40,04,60,149.04",
    "2018-19": "1,73,98,22,83,458.77",
    "2019-20-partial": "23,46,16,52,100.10",
}

for _key, _rows in _RS304_DONORS.items():
    _fy = _key.replace("-partial", "")
    _partial = _key.endswith("-partial")
    for _cty, _amt in _rows:
        DONOR_ROWS.append({
            "donor_country": _cty, "financial_year": _fy,
            "amount_str": _amt, "unit": "rupee", "source_id": "rs304",
            "table_ref": "Annexure-II: Country of Donors Foreign Contribution "
                         "(in Rupees), Year: %s" % _fy,
            "notes": "PARTIAL YEAR: ARs as on 16.03.2021; deadline extended "
                     "to 30.06.2021." if _partial else
                     "Excludes donor details < Rs 20,000 per Form FC-4.",
        })
    DONOR_ROWS.append({
        "donor_country": "ALL-COUNTRIES-TOTAL", "financial_year": _fy,
        "amount_str": _RS304_DONOR_TOTALS[_key], "unit": "rupee",
        "source_id": "rs304",
        "table_ref": "Annexure-II total row, Year: %s" % _fy,
        "notes": "Stated total in source; excludes donor details < Rs 20,000." +
                 (" PARTIAL YEAR." if _partial else ""),
    })

# ---- BusinessLine / MHA JPC briefing: top donor countries 2024-25, Rs cr ---
for _cty, _amt in [("United States of America", "12113"),
                   ("United Kingdom", "2414"), ("Germany", "1782"),
                   ("Switzerland", "733"), ("Singapore", "669")]:
    DONOR_ROWS.append({
        "donor_country": _cty, "financial_year": "2024-25",
        "amount_str": _amt, "unit": "crore", "source_id": "bl_jpc",
        "table_ref": "Article text: top donor countries 2024-25",
        "notes": "Secondary reporting of MHA JPC briefing; top-5 only.",
    })

# ----------------------------------------------------------------------------
# EMISSION + VALIDATION
# ----------------------------------------------------------------------------
STATE_COLS = ["state", "financial_year", "metric", "total_fc_inr",
              "total_fc_original", "original_unit", "reporting_associations",
              "source_document", "source_url", "table_ref", "retrieved_date",
              "notes"]
CANCEL_COLS = ["state", "period", "cancelled_count", "source_document",
               "source_url", "table_ref", "retrieved_date"]
DONOR_COLS = ["donor_country", "financial_year", "total_fc_inr",
              "total_fc_original", "original_unit", "source_document",
              "source_url", "table_ref", "retrieved_date", "notes"]


def build_state_rows():
    out = []
    for r in STATE_ROWS:
        src = SOURCES[r["source_id"]]
        amount_inr = (str(inr(r["amount_str"], r["unit"]))
                      if r["amount_str"] else "")
        out.append({
            "state": r["state"], "financial_year": r["financial_year"],
            "metric": r["metric"], "total_fc_inr": amount_inr,
            "total_fc_original": r["amount_str"], "original_unit": r["unit"],
            "reporting_associations": r["reporting_associations"],
            "source_document": src["document"], "source_url": src["url"],
            "table_ref": r["table_ref"], "retrieved_date": TODAY,
            "notes": (r["notes"] + " " + src["notes"]).strip(),
        })
    return out


def build_cancellation_rows():
    src = SOURCES["rs3253"]
    return [{
        "state": st, "period": "2020 to 22.03.2023",
        "cancelled_count": n, "source_document": src["document"],
        "source_url": src["url"],
        "table_ref": "Annexure-III: State-wise number of registrations "
                     "cancelled during the last 3 years (2020-2023)",
        "retrieved_date": TODAY,
    } for st, n in CANCELLATION_ROWS]


def build_donor_rows():
    out = []
    for r in DONOR_ROWS:
        src = SOURCES[r["source_id"]]
        out.append({
            "donor_country": r["donor_country"],
            "financial_year": r["financial_year"],
            "total_fc_inr": str(inr(r["amount_str"], r["unit"])),
            "total_fc_original": r["amount_str"], "original_unit": r["unit"],
            "source_document": src["document"], "source_url": src["url"],
            "table_ref": r["table_ref"], "retrieved_date": TODAY,
            "notes": (r["notes"] + " " + src["notes"]).strip(),
        })
    return out


def write_csv(path, cols, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({c: ("" if r.get(c) is None else r[c]) for c in cols})


def write_json(path, rows):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)
        f.write("\n")


def validate(state_rows, donor_rows, cancel_rows):
    """Independent checks. Returns list of (ok, message)."""
    checks = []

    # 1. No duplicate (state, financial_year, metric, source_url) keys.
    keys = [(r["state"], r["financial_year"], r["metric"], r["source_url"])
            for r in state_rows]
    checks.append((len(keys) == len(set(keys)),
                   "no duplicate (state, fy, metric, source) keys"))

    # 2. (original amount x unit) == total_fc_inr for every row with an amount.
    bad = [r for r in state_rows
           if r["total_fc_inr"] and r["total_fc_original"] and
           str(inr(r["total_fc_original"], r["original_unit"]))
           != r["total_fc_inr"]]
    bad += [r for r in donor_rows
            if str(inr(r["total_fc_original"], r["original_unit"]))
            != r["total_fc_inr"]]
    checks.append((not bad, "amount conversion identity holds%s"
                   % ("; failures: %d" % len(bad) if bad else "")))

    # 3. State sums match stated annexure totals where a total exists.
    #    (LS328 totals exclude nothing; RS304 totals are stated rows.)
    def sum_states(rows, source_id, fy, metric="received", exclude=()):
        return sum(Decimal(r["total_fc_inr"]) for r in rows
                   if r["source_url"] == SOURCES[source_id]["url"]
                   and r["financial_year"] == fy and r["metric"] == metric
                   and r["state"] not in ("ALL-INDIA",) + tuple(exclude))

    def stated_total(rows, source_id, fy, metric="received"):
        return [r for r in rows
                if r["source_url"] == SOURCES[source_id]["url"]
                and r["financial_year"] == fy and r["metric"] == metric
                and r["state"] == "ALL-INDIA"]

    # LS328: totals are separate national rows. Tolerance Rs 1,000 (0.01 lakh)
    # per the documented rounding artifact in the source document.
    for fy in ("2009-10", "2010-11"):
        s = sum_states(state_rows, "ls328", fy)
        t = stated_total(state_rows, "ls328", fy)
        checks.append((len(t) == 1 and abs(s - Decimal(t[0]["total_fc_inr"]))
                       <= Decimal("1000.00"),
                       "ls328 %s: state sum %s vs stated %s (tol Rs 1,000)" %
                       (fy, s, t[0]["total_fc_inr"] if t else "MISSING")))
    # 2011-12: the gap between stated total and included state rows is
    # exactly the excluded Andaman & Nicobar row, per source arithmetic.
    s = sum_states(state_rows, "ls328", "2011-12")
    t = stated_total(state_rows, "ls328", "2011-12")
    gap = Decimal(t[0]["total_fc_inr"]) - s if t else None
    checks.append((t and abs(gap - Decimal("48915000.00")) <= Decimal("1000.00"),
                   "ls328 2011-12: stated-vs-included gap %s == excluded A&N "
                   "row (Rs 489.15 lakh)" % gap))
    # RS304: state sums vs stated annexure totals.
    for fy in ("2016-17", "2017-18", "2018-19", "2019-20"):
        s = sum_states(state_rows, "rs304", fy)
        t = stated_total(state_rows, "rs304", fy)
        checks.append((len(t) == 1 and abs(s - Decimal(t[0]["total_fc_inr"]))
                       <= Decimal("1.00"),
                       "rs304 %s: state sum %s vs stated %s" %
                       (fy, s, t[0]["total_fc_inr"] if t else "MISSING")))
    # Donor sums vs stated annexure-II totals.
    for fy in ("2016-17", "2017-18", "2018-19", "2019-20"):
        s = sum(Decimal(r["total_fc_inr"]) for r in donor_rows
                if r["source_url"] == SOURCES["rs304"]["url"]
                and r["financial_year"] == fy
                and r["donor_country"] != "ALL-COUNTRIES-TOTAL")
        t = [r for r in donor_rows
             if r["source_url"] == SOURCES["rs304"]["url"]
             and r["financial_year"] == fy
             and r["donor_country"] == "ALL-COUNTRIES-TOTAL"]
        checks.append((len(t) == 1 and abs(s - Decimal(t[0]["total_fc_inr"]))
                       <= Decimal("1.00"),
                       "donors %s: country sum %s vs stated %s" %
                       (fy, s, t[0]["total_fc_inr"] if t else "MISSING")))

    # 4. RS3253 cancellations sum to the 1,828 stated in the answer.
    cancel_sum = sum(r["cancelled_count"] for r in cancel_rows)
    checks.append((cancel_sum == 1828,
                   "rs3253 cancellations sum %d == stated 1828" % cancel_sum))

    # 5. Row-count sanity per official year.
    for sid, fy, metric, expect in [
        ("ls328", "2009-10", "received", 33),  # Daman & Diu absent in doc
        ("ls328", "2010-11", "received", 34),
        ("ls328", "2011-12", "received", 33),  # A&N excluded
        ("rs304", "2016-17", "received", 34),
        ("rs304", "2017-18", "received", 34),
        ("rs304", "2018-19", "received", 34),
        ("rs304", "2019-20", "received", 33),
        ("rs3253", "2019-20", "received", 34),
        ("rs3253", "2020-21", "received", 34),
        ("rs3253", "2021-22", "received", 34),
        ("rs3253", "2019-20", "utilized", 34),
        ("rs3253", "2020-21", "utilized", 34),
        ("rs3253", "2021-22", "utilized", 34),
    ]:
        n = sum(1 for r in state_rows
                if r["source_url"] == SOURCES[sid]["url"]
                and r["financial_year"] == fy and r["metric"] == metric
                and r["state"] != "ALL-INDIA")
        checks.append((n == expect, "%s %s %s: %d rows (expect %d)"
                       % (sid, fy, metric, n, expect)))
    return checks


def main():
    os.makedirs(REAL, exist_ok=True)
    state_rows = build_state_rows()
    cancel_rows = build_cancellation_rows()
    donor_rows = build_donor_rows()

    write_csv(os.path.join(REAL, "fcra_state_year.csv"), STATE_COLS,
              state_rows)
    write_json(os.path.join(REAL, "fcra_state_year.json"), state_rows)
    write_csv(os.path.join(REAL, "fcra_cancellations.csv"), CANCEL_COLS,
              cancel_rows)
    write_json(os.path.join(REAL, "fcra_cancellations.json"), cancel_rows)
    write_csv(os.path.join(REAL, "fcra_donor_country.csv"), DONOR_COLS,
              donor_rows)
    write_json(os.path.join(REAL, "fcra_donor_country.json"), donor_rows)

    print("wrote: %d state-year rows, %d cancellation rows, %d donor rows"
          % (len(state_rows), len(cancel_rows), len(donor_rows)))
    failed = 0
    for ok, msg in validate(state_rows, donor_rows, cancel_rows):
        print(("PASS " if ok else "FAIL ") + msg)
        failed += (not ok)
    if EXCLUDED:
        print("\nExcluded (honesty log):")
        for reason, detail in EXCLUDED:
            print("  - [%s] %s" % (reason, detail))
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
