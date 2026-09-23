import { stats, inr, distinctFys } from "@/lib/fcra";
import HomeClient from "./home-client";

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
          A mechanical, human-curated ledger of foreign contributions disclosed by
          Indian NGOs under the Foreign Contribution (Regulation) Act — Form FC-4
          filings as published on{" "}
          <a href="https://fcraonline.nic.in/">fcraonline.nic.in</a>. Every number
          cites its source. No AI-generated content.
        </p>
      </header>

      <Nav />

      <div className="banner">
        <strong>Sample dataset</strong> — 24 illustrative rows only. Bulk FCRA
        ingestion from the MHA dashboard is pending. Nothing on this page is a
        finding of wrongdoing. Flags are mechanical correlations; the rule for
        each flag is shown next to it.
      </div>

      <section>
        <div className="section-head">
          <span className="section-num">01</span>
          <h2>The Ledger</h2>
          <span className="stamp red">Form FC-4</span>
        </div>
        <HomeClient fys={distinctFys()} />
      </section>

      <section>
        <div className="section-head">
          <span className="section-num">02</span>
          <h2>Sample Statistics</h2>
          <span className="stamp red">Sample · n=24</span>
        </div>
        <div className="stats-strip">
          <div className="stat">
            <div className="num">{s.rows}</div>
            <div className="lbl">Filing rows (sample)</div>
          </div>
          <div className="stat">
            <div className="num">{s.ngos}</div>
            <div className="lbl">NGOs (sample)</div>
          </div>
          <div className="stat">
            <div className="num">{s.donors}</div>
            <div className="lbl">Foreign donors (sample)</div>
          </div>
          <div className="stat">
            <div className="num">{inr(s.total_inr)}</div>
            <div className="lbl">Total inflow (sample)</div>
          </div>
          <div className="stat">
            <div className="num">{s.fys}</div>
            <div className="lbl">Financial years (sample)</div>
          </div>
          <div className="stat">
            <div className="num">{s.flag_hits}</div>
            <div className="lbl">Mechanical flag hits (sample)</div>
          </div>
        </div>
        <p className="mono" style={{ marginTop: 12, fontSize: 13, color: "#5c5c5c" }}>
          All figures computed mechanically from the 24-row sample dataset. Bulk
          numbers will replace these once MHA ingestion ships.
        </p>
      </section>

      <section>
        <div className="section-head">
          <span className="section-num">03</span>
          <h2>Flag Rules — Read Before You Share</h2>
          <span className="stamp red">Mechanical only</span>
        </div>
        <div className="prose">
          <p>
            FCRA FLOW never alleges wrongdoing. Each flag below is a pure
            arithmetic test over published Form FC-4 filings. The formula is
            printed next to every flag, and the full methodology — including what
            is <em>not</em> claimed — is on the{" "}
            <a href="/methodology">methodology page</a>.
          </p>
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
      </section>

      <footer>
        <div className="section-head">
          <h2 className="serif" style={{ fontSize: 24 }}>FCRA FLOW</h2>
          <span className="stamp">No AI-generated content — human-curated disclosure</span>
        </div>
        <p className="fine">
          Source: Ministry of Home Affairs FCRA dashboard (fcraonline.nic.in),
          Form FC-4 annual returns. Sample data on this scaffold is illustrative;
          registration numbers are masked. Bulk ingestion is future work — no
          CAPTCHAs, access controls, logins, or paywalls are bypassed.
          Correlation is not causation; a flag is a question, not an accusation.
        </p>
        <p className="fine">MIT License. Built as a public-interest OSINT tool.</p>
      </footer>
    </>
  );
}
