import stateYearRows from "../data/real/fcra_state_year.json";
import arRows from "../data/real/fcra_mha_ar_state_year.json";
import donorRows from "../data/real/fcra_donor_country.json";
import cancellationRows from "../data/real/fcra_cancellations.json";

export interface StateYearRow {
  state: string;
  financial_year: string;
  metric: "received" | "utilized" | "active_ngos";
  total_fc_inr: string;
  total_fc_original: string;
  original_unit: string;
  reporting_associations: number | null;
  source_document: string;
  source_url: string;
  table_ref: string;
  notes: string;
  retrieved_date: string;
}

export interface DonorRow {
  donor_country: string;
  financial_year: string;
  total_fc_inr: string;
  total_fc_original: string;
  original_unit: string;
  source_document: string;
  source_url: string;
  table_ref: string;
  notes: string;
  retrieved_date: string;
}

export interface CancellationRow {
  state: string;
  period: string;
  cancelled_count: number;
  source_document: string;
  source_url: string;
  table_ref: string;
  retrieved_date: string;
}

export const REAL_ROW_COUNT =
  (stateYearRows as unknown[]).length +
  (arRows as unknown[]).length +
  (donorRows as unknown[]).length +
  (cancellationRows as unknown[]).length;

/** Parse the decimal-string INR amount. Empty string -> null (not zero). */
export function parseInr(s: string | null | undefined): number | null {
  if (s === null || s === undefined) return null;
  const t = s.trim();
  if (t === "") return null;
  const n = Number(t);
  return Number.isFinite(n) ? n : null;
}

/** Indian-style amount: crores for large figures, full grouping below ~Rs 1 cr. */
export function inrCr(n: number | null): string {
  if (n === null || !Number.isFinite(n)) return "—";
  if (Math.abs(n) >= 5_000_000) {
    const cr = n / 10_000_000;
    return "Rs. " + cr.toLocaleString("en-IN", { maximumFractionDigits: 0 }) + " cr";
  }
  return "Rs. " + Math.round(n).toLocaleString("en-IN");
}

/** Short inline citation labels for the six source documents. */
export function shortDoc(doc: string): string {
  if (doc.includes("No. 328")) return "LS USQ 328 (06.08.2013)";
  if (doc.includes("No. 457")) return "LS USQ 457 (15.09.2020)";
  if (doc.includes("No. 304")) return "RS SQ 304 (24.03.2021)";
  if (doc.includes("No. 3253")) return "RS USQ 3253 (29.03.2023)";
  if (doc.includes("PIB Backgrounder")) return "PIB backgrounder (22.07.2026)";
  if (doc.includes("BusinessLine")) return "MHA briefing via BusinessLine (19.09.2026)";
  const ar = doc.match(/MHA Annual Report (\d{4}-\d{2})/);
  if (ar) return `MHA AR ${ar[1]}`;
  return doc.slice(0, 40) + "…";
}

const SY = [...(stateYearRows as StateYearRow[]), ...(arRows as StateYearRow[])];
const DC = donorRows as DonorRow[];
const CX = cancellationRows as CancellationRow[];

export function realStates(): string[] {
  return [...new Set(SY.map((r) => r.state))]
    .filter((s) => s !== "ALL-INDIA")
    .sort((a, b) => a.localeCompare(b));
}

export function realFys(): string[] {
  const order = (fy: string) => Number(fy.slice(0, 4));
  return [...new Set(SY.map((r) => r.financial_year))].sort(
    (a, b) => order(a) - order(b)
  );
}

export interface StateFyPivot {
  state: string;
  fy: string;
  received: number | null;
  utilized: number | null;
  reporting: number | null;
  active: number | null;
  docs: { label: string; url: string }[];
}

/** Merge received/utilized/active_ngos rows for one state × FY. */
export function stateFyPivot(state: string, fy: string): StateFyPivot {
  const rows = SY.filter((r) => r.state === state && r.financial_year === fy);
  const by = (m: string) => rows.find((r) => r.metric === m);
  const received = by("received");
  const utilized = by("utilized");
  const active = by("active_ngos");
  const docs = new Map<string, string>();
  for (const r of rows) docs.set(r.source_document, r.source_url);
  return {
    state,
    fy,
    received: parseInr(received?.total_fc_inr),
    utilized: parseInr(utilized?.total_fc_inr),
    reporting:
      received?.reporting_associations ?? utilized?.reporting_associations ?? null,
    active: active?.reporting_associations ?? null,
    docs: [...docs.entries()].map(([d, u]) => ({ label: shortDoc(d), url: u })),
  };
}

export function allStateFyPivots(): StateFyPivot[] {
  const out: StateFyPivot[] = [];
  for (const fy of realFys())
    for (const st of realStates()) out.push(stateFyPivot(st, fy));
  return out;
}

export function allIndiaTotals(): StateFyPivot[] {
  const fys = [...new Set(SY.map((r) => r.financial_year))];
  return fys
    .map((fy) => stateFyPivot("ALL-INDIA", fy))
    .filter((p) => p.received !== null || p.utilized !== null || p.active !== null);
}

export function donorFys(): string[] {
  const order = (fy: string) => Number(fy.slice(0, 4));
  return [...new Set(DC.map((r) => r.financial_year))].sort(
    (a, b) => order(a) - order(b)
  );
}

export interface DonorFyRow extends DonorRow {
  amount: number;
  share: number | null;
}

export function donorTopN(fy: string, n = 10): { rows: DonorFyRow[]; fyTotal: number | null; doc: string; url: string } {
  const rows = DC.filter(
    (r) => r.financial_year === fy && r.donor_country !== "ALL-COUNTRIES-TOTAL"
  )
    .map((r) => ({ ...r, amount: parseInr(r.total_fc_inr) ?? 0 }))
    .sort((a, b) => b.amount - a.amount);
  const totalRow = DC.find(
    (r) => r.financial_year === fy && r.donor_country === "ALL-COUNTRIES-TOTAL"
  );
  const fyTotal = parseInr(totalRow?.total_fc_inr);
  const first = rows[0];
  return {
    rows: rows.slice(0, n).map((r) => ({
      ...r,
      share: fyTotal && fyTotal > 0 ? r.amount / fyTotal : null,
    })),
    fyTotal,
    doc: first?.source_document ?? "",
    url: first?.source_url ?? "",
  };
}

export function cancellationsSorted(): CancellationRow[] {
  return [...CX].sort((a, b) => b.cancelled_count - a.cancelled_count);
}

export function cancellationTotal(): number {
  return CX.reduce((s, r) => s + r.cancelled_count, 0);
}

export function cancellationDoc(): { doc: string; url: string; period: string } {
  const r = CX[0];
  return { doc: r.source_document, url: r.source_url, period: r.period };
}

export interface NationalRow {
  fy: string;
  amount: number | null;
  reporting: number | null;
  qualifier: string | null;
  label: string;
  url: string;
}

/** Per-source ALL-INDIA received rows, FY-ordered. Revised/conflicting pairs
 *  are kept as separate rows — never merged. */
export function nationalSeries(): NationalRow[] {
  const order = (fy: string) => Number(fy.slice(0, 4));
  return SY.filter((r) => r.state === "ALL-INDIA" && r.metric === "received")
    .map((r) => {
      const q = r.notes.match(/Document qualifier on the figure: '([^']+)'/);
      return {
        fy: r.financial_year,
        amount: parseInr(r.total_fc_inr),
        reporting: r.reporting_associations,
        qualifier: q ? q[1] : null,
        label: shortDoc(r.source_document),
        url: r.source_url,
      };
    })
    .sort((a, b) => order(a.fy) - order(b.fy) || a.label.localeCompare(b.label));
}

/** Distinct source short-labels per FY for the state-year dataset (gap audit). */
export function stateFySources(): { fy: string; docs: string[] }[] {
  return realFys().map((fy) => ({
    fy,
    docs: [
      ...new Set(
        SY.filter((r) => r.financial_year === fy).map((r) => shortDoc(r.source_document))
      ),
    ],
  }));
}
