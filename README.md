# FCRA FLOW — Foreign Funding Disclosure Tracker

A public-interest OSINT tool tracking India's FCRA foreign-funding disclosures:
which registered NGOs received how much foreign contribution, from which foreign
donors, in which financial year — with mechanical, fully-disclosed anomaly flags.

Same DNA as SIR-WATCH and Bonded-Leader: public disclosure made usable, every
figure traces to a cited source, nothing editorialized. Deliberately different
look: light paper brutalism (Georgia serif masthead, 3px rules, red stamps).

## Sources

- Ministry of Home Affairs FCRA dashboard: https://fcraonline.nic.in/
- Form FC-4: annual return of foreign contribution received and utilised.

## Honest status

**1,004 real validated rows live** in `data/real/`: 464 state/UT × FY
received+utilised rows (FY 2009-10–2024-25, with declared gaps for 2014-16 and
2022-24), 499 donor-country × FY rows (FY 2016-17–2019-20 + 2024-25 top 5),
32 state-wise registration-cancellation rows (2020–22.03.2023), and 9 all-India
national-total rows from MHA annual reports (FY 2010-11–2017-18, the only
public anchors for FY 2012-13–2013-14). Sources: parliamentary answers by MHA
ministers, MHA annual reports, a PIB backgrounder, and an MHA briefing via
BusinessLine — every row carries its source document. See
`docs/DATA_SOURCES.md` for the full provenance log.

The name-level Form FC-4 ledger remains a **24-row sample dataset** (masked
`12XXX1234X` reg numbers, illustrative values) until portal-gated name-level
rows are obtainable through legitimate means.

Standing rules (shared with SIR-WATCH): no publishing form-gated datasets
against their terms; no bypassing CAPTCHAs, access controls, logins, or paywalls.

## Mechanical flags

- `SPIKE` — Inflow Spike: `FY_total >= 3 x FY_previous_total`
- `CONCENTRATION` — Donor Concentration: `donor_amount / NGO_FY_total >= 0.80`
- `DORMANT_REVIVAL` — Dormant Revival: `FY_previous_total = 0 AND FY_total >= 50,00,000`

A flag is a mechanical correlation with the rule shown, never a finding of
wrongdoing. Correlation is not causation. See `/methodology`.

## Preview

![FCRA FLOW homepage](public/screenshot.png)

## Run

```bash
npm install
npm run dev   # http://localhost:3000
npm run build # production build
```

## License

MIT. See LICENSE.
