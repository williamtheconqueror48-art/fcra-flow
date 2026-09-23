import {
  REAL_ROW_COUNT,
  realFys,
  donorFys,
  cancellationTotal,
  cancellationsSorted,
} from "@/lib/real";

export default function DataPage() {
  const fys = realFys();
  const donorYears = donorFys();
  const canc = cancellationsSorted();

  return (
    <>
      <header className="masthead">
        <div className="masthead-row">
          <span className="dateline">FCRA FLOW · Dataset</span>
          <a href="/" className="stamp" style={{ textDecoration: "none" }}>
            ← Back to ledger
          </a>
        </div>
        <h1 className="wordmark" style={{ fontSize: "clamp(36px, 7vw, 72px)" }}>
          THE <span className="flow">DATASET</span>
        </h1>
      </header>

      <section>
        <div className="section-head">
          <span className="section-num">01</span>
          <h2>Real Aggregates</h2>
          <span className="stamp red">
            Real · n={REAL_ROW_COUNT.toLocaleString("en-IN")}
          </span>
        </div>
        <div className="cards">
          <div className="card">
            <h3>fcra_state_year.json — 464 rows</h3>
            <p className="mono">
              State/UT × financial-year × metric (received / utilised /
              active_ngos). FY 2009-10–2024-25; state-level gaps declared for
              2014-15–2015-16 and 2022-23–2023-24; FY 2019-20 partial. Every row
              carries source_document, source_url, table_ref.
            </p>
          </div>
          <div className="card">
            <h3>fcra_mha_ar_state_year.json — 9 rows</h3>
            <p className="mono">
              All-India national totals from MHA annual reports (FY 2010-11–
              2017-18), the only public source for national anchors in FY
              2012-13–2013-14. Revised pairs kept as separate per-source rows,
              never merged.
            </p>
          </div>
          <div className="card">
            <h3>fcra_donor_country.json — 499 rows</h3>
            <p className="mono">
              Donor-country × financial-year totals (rupees). FY{" "}
              {donorYears.slice(0, -1).join(", ")} full country lists from RS SQ
              304; FY {donorYears[donorYears.length - 1]} top 5 from the MHA
              briefing. Excludes donations below Rs. 20,000 per Form FC-4.
            </p>
          </div>
          <div className="card">
            <h3>fcra_cancellations.json — 32 rows</h3>
            <p className="mono">
              State-wise FCRA registrations cancelled, 2020 to 22.03.2023 —
              total {cancellationTotal().toLocaleString("en-IN")}. Highest:{" "}
              {canc[0].state} ({canc[0].cancelled_count.toLocaleString("en-IN")}).
              Source: RS USQ 3253, Annexure-III.
            </p>
          </div>
        </div>
        <div className="prose" style={{ marginTop: 16 }}>
          <p>
            Documents: Lok Sabha / Rajya Sabha questions answered by MHA
            ministers, MHA annual reports, a PIB backgrounder, and an MHA
            briefing via BusinessLine.
            Full provenance — what was attempted, what failed, per-row document
            links, and the coverage-gap audit — is in{" "}
            <span className="mono">docs/DATA_SOURCES.md</span> in the repository.
            The name-level Form FC-4 ledger on the homepage is a 24-row
            illustrative sample (<span className="mono">data/sample/</span>).
          </p>
        </div>
      </section>

      <footer>
        <p className="fine">
          <a href="/">Back to the ledger</a> · MIT License.
        </p>
      </footer>
    </>
  );
}
