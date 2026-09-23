import { flagDefinitions } from "@/lib/fcra";

export default function Methodology() {
  const defs = flagDefinitions();
  return (
    <>
      <header className="masthead">
        <div className="masthead-row">
          <span className="dateline">FCRA FLOW · Methodology</span>
          <a href="/" className="stamp" style={{ textDecoration: "none" }}>
            ← Back to ledger
          </a>
        </div>
        <h1 className="wordmark" style={{ fontSize: "clamp(36px, 7vw, 72px)" }}>
          HOW THE FLAGS <span className="flow">WORK</span>
        </h1>
      </header>

      <section>
        <div className="section-head">
          <span className="section-num">A</span>
          <h2>Sources</h2>
        </div>
        <div className="prose">
          <p>
            The primary source is the Ministry of Home Affairs FCRA dashboard at{" "}
            <a href="https://fcraonline.nic.in/">fcraonline.nic.in</a> — the public
            portal where NGOs registered under the Foreign Contribution
            (Regulation) Act, 2010 file their annual returns.
          </p>
          <p>
            The return form is <strong>Form FC-4</strong>: the annual account of
            foreign contribution received and utilised. FCRA FLOW tracks the
            "received" side — which foreign donor gave how much, to which
            registered NGO, in which financial year, for what declared purpose.
          </p>
          <p>
            The current scaffold ships with a 24-row <strong>sample dataset</strong>{" "}
            of illustrative filings with masked registration numbers. Bulk
            ingestion from the MHA dashboard is future work. The standing rule
            applies: no CAPTCHAs, access controls, logins, or paywalls are ever
            bypassed to collect data.
          </p>
        </div>
      </section>

      <section>
        <div className="section-head">
          <span className="section-num">B</span>
          <h2>Mechanical Flag Rules</h2>
          <span className="stamp red">Exact formulas</span>
        </div>
        <div className="prose">
          <p>
            Every flag on this site is the output of a fixed arithmetic test.
            There is no scoring model, no AI, no discretion. The formula is
            printed next to each flag everywhere it appears.
          </p>
        </div>
        {defs.map((d) => (
          <div className="formula-box" key={d.id}>
            <span className="fname">
              {d.id} — {d.name}
            </span>
            <span className="formula">{d.formula}</span>
            {d.rule}
          </div>
        ))}
      </section>

      <section>
        <div className="section-head">
          <span className="section-num">C</span>
          <h2>Limitations</h2>
        </div>
        <div className="prose">
          <p>
            1. <strong>Sample only.</strong> The 24-row scaffold is illustrative.
            Real analysis requires the full Form FC-4 corpus.
          </p>
          <p>
            2. <strong>Received, not utilised.</strong> These are inflow figures.
            They say nothing about how money was spent.
          </p>
          <p>
            3. <strong>Currency and amendments.</strong> Figures are in INR as
            declared. Revised or amended filings supersede earlier ones.
          </p>
          <p>
            4. <strong>Names are messy.</strong> Donor and NGO names are
            self-declared; spelling variants can split or merge entities until
            entity resolution is added.
          </p>
        </div>
      </section>

      <section>
        <div className="section-head">
          <span className="section-num">D</span>
          <h2>What Is NOT Claimed</h2>
          <span className="stamp solid-red">Read this</span>
        </div>
        <div className="prose">
          <p>
            A flag is <strong>not</strong> a finding of wrongdoing, illegality,
            or impropriety. It is a mechanical correlation — a row that satisfies
            a published arithmetic rule. Legitimate reasons exist for every
            pattern flagged here: a multi-year grant disbursing at once can trip
            SPIKE; a single committed donor can trip CONCENTRATION; a new
            programme can trip DORMANT_REVIVAL.
          </p>
          <p>
            FCRA FLOW makes no allegation against any NGO or donor named here.
            Sample rows are illustrative and any resemblance to real filings is
            coincidental until bulk ingestion replaces them with cited records.
          </p>
        </div>
      </section>

      <footer>
        <p className="fine">
          Questions about the rules? The formulas above are the complete
          specification. <a href="/">Back to the ledger</a>.
        </p>
      </footer>
    </>
  );
}
