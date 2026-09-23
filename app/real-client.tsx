"use client";

import { useMemo, useState } from "react";
import { realStates, realFys, stateFyPivot, inrCr } from "@/lib/real";

export default function RecordTable() {
  const states = realStates();
  const fys = realFys();
  const [state, setState] = useState("");
  const [fy, setFy] = useState(fys[fys.length - 1]);

  const rows = useMemo(() => {
    const sts = state ? [state] : states;
    return sts
      .map((s) => stateFyPivot(s, fy))
      .filter((p) => p.received !== null || p.utilized !== null);
  }, [state, fy, states]);

  return (
    <div>
      <form
        className="search-grid"
        onSubmit={(e) => e.preventDefault()}
        style={{ marginBottom: 8 }}
      >
        <select
          value={fy}
          onChange={(e) => setFy(e.target.value)}
          aria-label="Financial year"
        >
          {fys.map((f) => (
            <option key={f} value={f}>
              FY {f}
            </option>
          ))}
        </select>
        <select
          value={state}
          onChange={(e) => setState(e.target.value)}
          aria-label="State or UT"
        >
          <option value="">All states / UTs</option>
          {states.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
      </form>
      <p className="result-meta">
        {rows.length} records · FY {fy} · real aggregates answered in Parliament
        and released by MHA — not estimates
      </p>
      <div className="table-wrap">
        <table className="ledger">
          <thead>
            <tr>
              <th>State / UT</th>
              <th>FY</th>
              <th>Received</th>
              <th>Utilised</th>
              <th>Reporting NGOs</th>
              <th>Source</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.state}>
                <td>
                  <strong>{r.state}</strong>
                </td>
                <td className="mono">{r.fy}</td>
                <td className="amt">{inrCr(r.received)}</td>
                <td className="amt">{inrCr(r.utilized)}</td>
                <td className="mono">
                  {r.reporting !== null
                    ? r.reporting.toLocaleString("en-IN")
                    : "—"}
                </td>
                <td>
                  {r.docs.map((d, i) => (
                    <span key={i}>
                      {i > 0 && <br />}
                      <a href={d.url} target="_blank" rel="noreferrer">
                        {d.label} ↗
                      </a>
                    </span>
                  ))}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="mono" style={{ fontSize: 13, color: "#5c5c5c", marginTop: 8 }}>
        <strong>Coverage &amp; gaps:</strong> state-level figures missing for FY
        2014-15–2015-16 and FY 2022-23–2023-24 (no source publishes them).
        All-India national totals for FY 2012-13 and FY 2013-14 come from MHA
        annual reports (see National Totals below) — no state split exists for
        those years. FY 2019-20 is partial — only annual returns filed as on
        16.03.2021 were tabulated. Donor-country rows exclude donations below
        Rs. 20,000 per Form FC-4.
      </p>
    </div>
  );
}
