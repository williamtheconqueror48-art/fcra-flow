"use client";

import { useEffect, useState } from "react";

interface FlagHit {
  filing_id: string;
  flag_id: string;
  flag_name: string;
  formula: string;
  detail: string;
}

interface Filing {
  id: string;
  ngo_name: string;
  fcra_reg_no: string;
  donor_name: string;
  donor_country: string;
  amount_inr: number;
  fy: string;
  purpose: string;
  source_url: string;
  filing_date: string;
  flags: FlagHit[];
}

function inr(n: number): string {
  return "Rs. " + n.toLocaleString("en-IN");
}

export default function HomeClient({ fys }: { fys: string[] }) {
  const [q, setQ] = useState("");
  const [type, setType] = useState("all");
  const [year, setYear] = useState("");
  const [rows, setRows] = useState<Filing[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);

  async function runSearch() {
    setLoading(true);
    try {
      const p = new URLSearchParams({ q, type, year });
      const r = await fetch(`/api/search?${p.toString()}`);
      const j = await r.json();
      setRows(j.results ?? []);
      setTotal(j.total ?? 0);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    runSearch();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div>
      <form
        className="search-grid"
        onSubmit={(e) => {
          e.preventDefault();
          runSearch();
        }}
      >
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Search NGO, donor, or country…"
          aria-label="Search"
        />
        <select
          value={type}
          onChange={(e) => setType(e.target.value)}
          aria-label="Search type"
        >
          <option value="all">All fields</option>
          <option value="ngo">NGO name</option>
          <option value="donor">Donor name</option>
        </select>
        <select
          value={year}
          onChange={(e) => setYear(e.target.value)}
          aria-label="Financial year"
        >
          <option value="">All years</option>
          {fys.map((f) => (
            <option key={f} value={f}>
              FY {f}
            </option>
          ))}
        </select>
        <button type="submit">Search</button>
      </form>

      <p className="result-meta">
        {loading
          ? "Searching…"
          : `${total} filing${total === 1 ? "" : "s"} · sample dataset`}
      </p>

      <div className="table-wrap">
        <table className="ledger">
          <thead>
            <tr>
              <th>ID</th>
              <th>NGO (masked reg.)</th>
              <th>Donor / Country</th>
              <th>FY</th>
              <th>Amount</th>
              <th>Purpose</th>
              <th>Source</th>
              <th>Flags</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.id} className={r.amount_inr === 0 ? "nil-row" : ""}>
                <td className="mono">{r.id}</td>
                <td>
                  <strong>{r.ngo_name}</strong>
                  <br />
                  <span className="mono" style={{ fontSize: 12 }}>
                    {r.fcra_reg_no}
                  </span>
                </td>
                <td>
                  {r.donor_name}
                  <br />
                  <span style={{ color: "#5c5c5c", fontSize: 13 }}>
                    {r.donor_country}
                  </span>
                </td>
                <td className="mono">{r.fy}</td>
                <td className="amt">
                  {r.amount_inr === 0 ? "NIL" : inr(r.amount_inr)}
                </td>
                <td>{r.purpose}</td>
                <td>
                  <a href={r.source_url} target="_blank" rel="noreferrer">
                    fcraonline ↗
                  </a>
                  <br />
                  <span className="mono" style={{ fontSize: 12 }}>
                    {r.filing_date}
                  </span>
                </td>
                <td>
                  {r.flags.length === 0 ? (
                    <span style={{ color: "#5c5c5c", fontSize: 13 }}>—</span>
                  ) : (
                    r.flags.map((fl) => (
                      <div key={fl.flag_id}>
                        <span className="flag-tag">{fl.flag_name}</span>
                        <div className="flag-detail">{fl.detail}</div>
                        <div className="flag-detail">Rule: {fl.formula}</div>
                      </div>
                    ))
                  )}
                </td>
              </tr>
            ))}
            {rows.length === 0 && !loading && (
              <tr>
                <td colSpan={8} style={{ padding: 20 }}>
                  No filings match. Try another name, donor, or year.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
