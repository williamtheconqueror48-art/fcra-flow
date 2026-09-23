import { stats, flagDefinitions } from "@/lib/fcra";

export default function DataPage() {
  const s = stats();
  const defs = flagDefinitions();
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
          <h2>Sample Filings</h2>
          <span className="stamp red">Sample · n={s.rows}</span>
        </div>
        <div className="cards">
          <div className="card">
            <h3>sample_fcra.json</h3>
            <p className="mono">
              24 illustrative filing rows · fields: id, ngo_name, fcra_reg_no
              (masked), donor_name, donor_country, amount_inr, fy, purpose,
              source_url, filing_date. NIL filings are included as amount 0.
            </p>
          </div>
          <div className="card">
            <h3>flags.json</h3>
            <p className="mono">
              {defs.length} mechanical flag definitions · each with an exact
              rule and formula: {defs.map((d) => d.id).join(", ")}.
            </p>
          </div>
          <div className="card">
            <h3>Provenance</h3>
            <p className="mono">
              Schema mirrors Form FC-4 fields as published on
              fcraonline.nic.in. Sample values are illustrative; registration
              numbers are masked (12XXX1234X pattern).
            </p>
          </div>
        </div>
      </section>

      <section>
        <div className="section-head">
          <span className="section-num">02</span>
          <h2>Download</h2>
        </div>
        <div className="prose">
          <p>
            The sample CSV mirrors the JSON fields exactly, so any bulk
            ingestion can reuse this schema unchanged.
          </p>
          <p>
            <a
              href={
                "data:text/csv;charset=utf-8," +
                encodeURIComponent(
                  "id,ngo_name,fcra_reg_no,donor_name,donor_country,amount_inr,fy,purpose,source_url,filing_date\n" +
                    [
                      "F001,Helping Hands Foundation,04XXX1278X,Open Horizon Fund,United States,5000000,2021-22,Educational,https://fcraonline.nic.in/,2022-09-15",
                      "F009,Helping Hands Foundation,04XXX1278X,Open Horizon Fund,United States,18000000,2022-23,Educational,https://fcraonline.nic.in/,2023-09-12",
                      "F015,New Dawn Welfare Association,03XXX7712X,Liberty Grant Corp,United States,6000000,2022-23,Social,https://fcraonline.nic.in/,2023-10-30",
                      "F021,Global Health Initiative India,12XXX8893X,MedCare Global,United States,20000000,2023-24,Medical,https://fcraonline.nic.in/,2024-08-22",
                    ].join("\n")
                )
              }
              download="fcra_flow_sample.csv"
            >
              ⬇ Download 4-row sample CSV
            </a>{" "}
            <span className="stamp" style={{ marginLeft: 8 }}>Sample</span>
          </p>
          <p className="mono" style={{ fontSize: 13, color: "#5c5c5c" }}>
            Full 24-row sample lives at data/sample_fcra.json in the repository.
          </p>
        </div>
      </section>

      <section>
        <div className="section-head">
          <span className="section-num">03</span>
          <h2>Roadmap</h2>
        </div>
        <div className="prose">
          <p>
            1. Bulk ingestion of Form FC-4 filings from the MHA dashboard
            (public pages only; no access-control bypass). 2. Entity resolution
            for donor/NGO name variants. 3. Static-shard publishing via
            jsDelivr, matching the SIR-WATCH $0 architecture. 4. Year-over-year
            donor graph: donor → NGO network view.
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
