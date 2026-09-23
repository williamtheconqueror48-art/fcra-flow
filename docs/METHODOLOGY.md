# Methodology — FCRA FLOW

## What the tool tracks

Foreign contributions disclosed by Indian NGOs registered under the Foreign
Contribution (Regulation) Act, 2010: which registered association received how
much, from which foreign donor, in which financial year, for what declared
purpose — as filed in **Form FC-4** annual returns on
https://fcraonline.nic.in/.

## Mechanical flags (the complete specification)

There is no scoring model, no AI, no discretion. Each flag is a fixed
arithmetic test; the formula is printed next to every flag in the UI.

| ID | Name | Formula | Meaning |
|----|------|---------|---------|
| SPIKE | Inflow Spike | `FY_total >= 3 × FY_previous_total` (previous FY total > 0) | NGO's total foreign inflow in a FY is at least 3× the previous FY |
| CONCENTRATION | Donor Concentration | `donor_amount / NGO_FY_total >= 0.80` | One foreign donor provides ≥80% of an NGO's FY inflow |
| DORMANT_REVIVAL | Dormant Revival | `FY_previous_total = 0 AND FY_total >= 50,00,000` | NIL filing in previous FY, then ≥ Rs. 50 lakh this FY |

Flags attach per filing row: SPIKE and DORMANT_REVIVAL attach to every row of
the NGO's flagged FY; CONCENTRATION attaches to the dominant donor's row.
A filing can carry multiple flags (e.g. a 100% single-donor inflow that is
also ≥3× the previous FY).

## What is NOT claimed

A flag is **not** a finding of wrongdoing. Legitimate reasons exist for every
pattern: a multi-year grant disbursing at once trips SPIKE; a single committed
donor trips CONCENTRATION; a new programme trips DORMANT_REVIVAL. Correlation
is not causation.

## Data handling rules

- Sample rows (`data/sample/`) and real rows (`data/real/`) are never mixed
  silently; the UI labels which dataset it is reading.
- Registration numbers are masked in public views (`12XXX1234X` pattern).
- Every real row must carry a per-row `source_url` before it ships.
- No CAPTCHA / login / paywall bypass, ever. If the portal won't serve it
  publicly, it doesn't go in.
