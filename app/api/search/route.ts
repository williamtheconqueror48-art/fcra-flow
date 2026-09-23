import { NextRequest, NextResponse } from "next/server";
import { searchFilings } from "@/lib/fcra";

export async function GET(req: NextRequest) {
  const sp = req.nextUrl.searchParams;
  const q = sp.get("q") ?? "";
  const typeParam = sp.get("type") ?? "all";
  const year = sp.get("year") ?? "";
  const type = typeParam === "ngo" || typeParam === "donor" ? typeParam : "all";
  const results = searchFilings(q, type, year);
  return NextResponse.json({ total: results.length, results });
}
