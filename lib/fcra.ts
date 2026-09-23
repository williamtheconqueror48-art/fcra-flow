import sampleData from "../data/sample/sample_fcra.json";
import flagDefs from "../data/flags.json";

export interface Filing {
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
}

export interface FlagDef {
  id: string;
  name: string;
  rule: string;
  formula: string;
}

export interface FlagHit {
  filing_id: string;
  flag_id: string;
  flag_name: string;
  formula: string;
  detail: string;
}

export interface FilingWithFlags extends Filing {
  flags: FlagHit[];
}

const FY_ORDER = ["2021-22", "2022-23", "2023-24"];

export function allFilings(): Filing[] {
  return sampleData as Filing[];
}

export function flagDefinitions(): FlagDef[] {
  return flagDefs as FlagDef[];
}

function prevFY(fy: string): string | null {
  const i = FY_ORDER.indexOf(fy);
  return i > 0 ? FY_ORDER[i - 1] : null;
}

/** Total inflow per NGO per FY (NIL rows count as 0). */
export function ngoFyTotals(): Map<string, number> {
  const m = new Map<string, number>();
  for (const f of allFilings()) {
    const k = `${f.ngo_name}||${f.fy}`;
    m.set(k, (m.get(k) ?? 0) + f.amount_inr);
  }
  return m;
}

/** Previous FY total per NGO, or null when the NGO has no earlier record. */
function previousFyTotal(ngo: string, fy: string): number | null {
  const p = prevFY(fy);
  if (!p) return null;
  const totals = ngoFyTotals();
  // A previous FY with no rows at all is treated as no baseline (not as NIL).
  const hasRow = allFilings().some((f) => f.ngo_name === ngo && f.fy === p);
  if (!hasRow) return null;
  return totals.get(`${ngo}||${p}`) ?? 0;
}

/** Attach mechanical flags to a filing row. Pure arithmetic, no judgement. */
export function computeFlagsFor(f: Filing): FlagHit[] {
  const hits: FlagHit[] = [];
  const totals = ngoFyTotals();
  const fyTotal = totals.get(`${f.ngo_name}||${f.fy}`) ?? 0;
  const prev = previousFyTotal(f.ngo_name, f.fy);

  // SPIKE: FY_total >= 3 x previous FY total (previous must be > 0)
  if (prev !== null && prev > 0 && fyTotal >= 3 * prev) {
    hits.push({
      filing_id: f.id,
      flag_id: "SPIKE",
      flag_name: "Inflow Spike",
      formula: "FY_total >= 3 x FY_previous_total",
      detail: `FY ${f.fy} total ${inr(fyTotal)} is ${(fyTotal / prev).toFixed(2)}x FY ${prevFY(f.fy)} total ${inr(prev)}.`,
    });
  }

  // CONCENTRATION: single donor >= 80% of NGO's FY total (only real donor rows)
  if (f.amount_inr > 0 && fyTotal > 0 && f.amount_inr / fyTotal >= 0.8) {
    hits.push({
      filing_id: f.id,
      flag_id: "CONCENTRATION",
      flag_name: "Donor Concentration",
      formula: "donor_amount / NGO_FY_total >= 0.80",
      detail: `${f.donor_name} provided ${((f.amount_inr / fyTotal) * 100).toFixed(1)}% of ${f.ngo_name}'s FY ${f.fy} inflow.`,
    });
  }

  // DORMANT_REVIVAL: previous FY NIL (0) and current FY >= 50L
  if (prev !== null && prev === 0 && fyTotal >= 5000000) {
    hits.push({
      filing_id: f.id,
      flag_id: "DORMANT_REVIVAL",
      flag_name: "Dormant Revival",
      formula: "FY_previous_total = 0 AND FY_total >= 50,00,000",
      detail: `NIL filing in FY ${prevFY(f.fy)}; FY ${f.fy} inflow ${inr(fyTotal)} >= 50,00,000.`,
    });
  }

  return hits;
}

export function inr(n: number): string {
  return "Rs. " + n.toLocaleString("en-IN");
}

export function searchFilings(
  q: string,
  type: "ngo" | "donor" | "all" = "all",
  year = ""
): FilingWithFlags[] {
  const needle = q.trim().toLowerCase();
  return allFilings()
    .filter((f) => {
      if (year && f.fy !== year) return false;
      if (!needle) return true;
      if (type === "ngo") return f.ngo_name.toLowerCase().includes(needle);
      if (type === "donor") return f.donor_name.toLowerCase().includes(needle);
      return (
        f.ngo_name.toLowerCase().includes(needle) ||
        f.donor_name.toLowerCase().includes(needle) ||
        f.donor_country.toLowerCase().includes(needle)
      );
    })
    .map((f) => ({ ...f, flags: computeFlagsFor(f) }));
}

export interface Stats {
  rows: number;
  ngos: number;
  donors: number;
  total_inr: number;
  fys: number;
  flag_hits: number;
}

export function stats(): Stats {
  const filings = allFilings();
  const ngos = new Set(filings.map((f) => f.ngo_name));
  const donors = new Set(
    filings.filter((f) => f.amount_inr > 0).map((f) => f.donor_name)
  );
  const total_inr = filings.reduce((s, f) => s + f.amount_inr, 0);
  const flag_hits = filings.reduce(
    (s, f) => s + computeFlagsFor(f).length,
    0
  );
  return {
    rows: filings.length,
    ngos: ngos.size,
    donors: donors.size,
    total_inr,
    fys: FY_ORDER.length,
    flag_hits,
  };
}

export function distinctFys(): string[] {
  return FY_ORDER;
}
