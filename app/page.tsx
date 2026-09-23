import { stats, inr, distinctFys } from "@/lib/fcra";
import {
  donorTopN,
  donorFys,
  cancellationTotal,
  cancellationDoc,
  inrCr,
  shortDoc,
  nationalSeries,
  REAL_ROW_COUNT,
} from "@/lib/real";
import HomeClient from "./home-client";
import RecordTable from "./real-client";

function Nav() {
  return (
    <nav className="nav">
      <a href="/">Ledger</a>
      <a href="/methodology">Methodology</a>
      <a href="/data">Data</a>
    </nav>
  );
}

export default function Home() {
  const s = stats();
  const donorYears = donorFys();
  const latestDonorFy = donorYears[donorYears.length - 1];
  const donors = donorTopN(latestDonorFy, 5);
  const cancTotal = cancellationTotal();
  const cancSrc = cancellationDoc();

  return (
    <>
      <header className="masthead">
        <div className="masthead-row">
          <span className="dateline">New Delhi · {new Date().toDateString()}</span>
          <span className="stamp">Public Record</span>
        </div>
        <h1 className="wordmark">
          FCRA <span className="flow">FLOW</span>
        </h1>
        <p className="tagline">
          Foreign contributions received by Indian NGOs under the Foreign
          Contribution (Regulation) Act — state-level and donor-country
          aggregates answered in Parliament and released by MHA. Every number
          cites its source. No AI-generated content.
        </p>
      </header>

      <Nav />

      <section>
        <div className="section-head">
          <span className="section-num">01</span>
          <h2>The Record</h2>
          <span className="stamp red">Real · {REAL_ROW_COUNT.toLocaleString("en-IN")} rows</span>
        </div>
        <RecordTable />
        <h3 className="mono" style={{ marginTop: 24, fontSize: 15 }}>
          NATIONAL TOTALS — ALL INDIA, PER SOURCE
        </h3>
        <p className="mono" style={{ fontSize: 13, color: "#5c5c5c" }}>
          Every all-India figure ever published, kept as separate per-source
          rows. Revised pairs (e.g. FY 2011-12, 2012-13) show the earlier and
          the revised figure side by side — the documents disagree, so we do
          not pick one.
        </p>
        <div className="table-wrap">
          <table className="ledger">
            <thead>
              <tr>
                <th>FY</th>
                <th>Received</th>
                <th>Reporting NGOs</th>
                <th>Source</th>
              </tr>
            </thead>
            <tbody>
              {nationalSeries().map((r, i) => (
                <tr key={i}>
                  <td className="mono">{r.fy}</td>
                  <td className="amt">
                    {r.qualifier ? r.qualifier + " " : ""}
                    {inrCr(r.amount)}
                  </td>
                  <td className="mono">
                    {r.reporting !== null
                      ? r.reporting.toLocaleString("en-IN")
                      : "—"}
                  </td>
                  <td>
                    <a href={r.url} target="_blank" rel="noreferrer">
                      {r.label} ↗
                    </a>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section>
        <div className="stats-strip">
          {donors.rows.map((r) => (
            <div className="stat" key={r.donor_country}>
              <div className="num" style={{ fontSize: 20 }}>
                {inrCr(r.amount)}
              </div>
              <div className="lbl">
                {r.donor_country} · FY {r.financial_year}
              </div>
            </div>
          ))}
        </div>
        <p className="mono" style={{ fontSize: 13, color: "#5c5c5c", marginTop: 8 }}>
          Top {donors.rows.length} donor countries, FY {latestDonorFy} — source:{" "}
          <a href={donors.url} target="_blank" rel="noreferrer">
            {shortDoc(donors.doc)} ↗
          </a>
          . · {cancTotal.toLocaleString("en-IN")} FCRA registrations cancelled,{" "}
          {cancSrc.period} — source:{" "}
          <a href={cancSrc.url} target="_blank" rel="noreferrer">
            {shortDoc(cancSrc.doc)} ↗
          </a>
          .
        </p>
      </section>

      <div className="banner" style={{ marginTop: 8 }}>
        <strong>Sample dataset below</strong> — 24 illustrative Form FC-4
        name-level rows for the flag demo. Not MHA records.
      </div>

      <section>
        <div className="section-head">
          <span className="section-num">02</span>
          <h2>The Ledger (Sample)</h2>
          <span className="stamp red">Sample · n=24</span>
        </div>
        <HomeClient fys={distinctFys()} />
        <p className="mono" style={{ marginTop: 12, fontSize: 13, color: "#5c5c5c" }}>
          Sample stats: {s.rows} rows · {s.ngos} NGOs · {s.donors} donors ·{" "}
          {inr(s.total_inr)} total inflow · {s.flag_hits} flag hits. Computed
          mechanically from the sample dataset.
        </p>
      </section>

      <section>
        <div className="section-head">
          <span className="section-num">03</span>
          <h2>Flag Rules — Read Before You Share</h2>
          <span className="stamp red">Mechanical only</span>
        </div>
        <div className="formula-box">
          <span className="fname">SPIKE — Inflow Spike</span>
          <span className="formula">FY_total &gt;= 3 x FY_previous_total</span>
          NGO's total foreign inflow in a FY is at least 3x the previous FY.
        </div>
        <div className="formula-box">
          <span className="fname">CONCENTRATION — Donor Concentration</span>
          <span className="formula">donor_amount / NGO_FY_total &gt;= 0.80</span>
          One foreign donor provides 80%+ of an NGO's FY inflow.
        </div>
        <div className="formula-box">
          <span className="fname">DORMANT_REVIVAL — Dormant Revival</span>
          <span className="formula">FY_previous_total = 0 AND FY_total &gt;= 50,00,000</span>
          NIL filing in the previous FY, then at least Rs. 50 lakh this FY.
        </div>
        <div className="prose">
          <p>
            FCRA FLOW never alleges wrongdoing. A flag is a question, not an
            accusation. Full methodology — including what is <em>not</em>{" "}
            claimed — is on the <a href="/methodology">methodology page</a>.
          </p>
        </div>
      </section>

      <footer>
        <div className="section-head">
          <h2 className="serif" style={{ fontSize: 24 }}>FCRA FLOW</h2>
          <span className="stamp">No AI-generated content — human-curated disclosure</span>
        </div>
        <p className="fine">
          Sources: Lok Sabha / Rajya Sabha questions (MHA ministers), MHA
          annual reports, PIB backgrounder, MHA briefing via BusinessLine —
          every real row carries its source document. Name-level sample rows
          are illustrative; registration numbers are masked. No CAPTCHAs,
          access controls, logins, or paywalls were bypassed. Correlation is
          not causation.
        </p>
        <p className="fine">MIT License. Built as a public-interest OSINT tool.</p>
      </footer>
    </>
  );
}
