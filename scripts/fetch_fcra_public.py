#!/usr/bin/env python3
"""Polite plain-GET fetcher for MHA FCRA portal public static documents.

HARD RULES (standing, non-negotiable):
- Only plain public HTTP(S) GET requests.
- No CAPTCHA bypass, no login bypass, no paywall circumvention, no session
  spoofing. If a resource requires interaction, it is skipped and logged.
- Polite rate: one request at a time with a sleep between requests.
- Research User-Agent identifying the public-interest purpose.

Status (2026-09-23): the live portal did not answer plain requests from the
sandbox network (empty reply before any HTTP status on both http and https).
This script is the documented method for a future network where the host
answers; it has NOT yet succeeded against the live portal.

Usage:
    python3 scripts/fetch_fcra_public.py --out data/real/raw
"""

import argparse
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

UA = "FCRA-FLOW-research/1.0 (public-interest OSINT; repo: fcra-flow)"

# Public static documents only — no interactive/dashboard endpoints.
TARGETS = [
    (
        "mha_fcra_faq_2022",
        "https://fcraonline.nic.in/Home/PDF_Doc/fc_faq_04102022.pdf",
    ),
]

POLITE_DELAY_S = 5


def fetch(url: str, timeout: int = 60) -> bytes:
    req = Request(url, headers={"User-Agent": UA})
    with urlopen(req, timeout=timeout) as resp:
        if resp.status != 200:
            raise RuntimeError(f"HTTP {resp.status} for {url}")
        return resp.read()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, help="output directory for raw files")
    args = ap.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    log = []

    for name, url in TARGETS:
        entry = {
            "name": name,
            "url": url,
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
            "ok": False,
        }
        try:
            payload = fetch(url)
            digest = hashlib.sha256(payload).hexdigest()
            dest = out / f"{name}.pdf"
            dest.write_bytes(payload)
            entry.update(
                ok=True,
                sha256=digest,
                bytes=len(payload),
                path=str(dest),
            )
            print(f"OK  {name}: {len(payload)} bytes sha256={digest[:16]}...")
        except Exception as e:  # noqa: BLE001 - honest failure log
            entry["error"] = f"{type(e).__name__}: {e}"
            print(f"FAIL {name}: {entry['error']}")
        log.append(entry)
        time.sleep(POLITE_DELAY_S)

    (out / "ingestion_log.json").write_text(json.dumps(log, indent=2))
    print(f"Wrote {(out / 'ingestion_log.json')}")


if __name__ == "__main__":
    main()
