# Data sources — FCRA FLOW

Last updated: 2026-09-23.

## Primary source

- **MHA FCRA dashboard / portal:** https://fcraonline.nic.in/
- **Return form:** Form FC-4 — annual return of foreign contribution received
  and utilised, filed online per Rule 17 of the Foreign Contribution
  (Regulation) Rules, 2011. Filing is mandatory every financial year
  (1 April – 31 March), including NIL returns.
- **Background reference:** MHA FAQ on FCRA filing (Form FC-4),
  https://fcraonline.nic.in/Home/PDF_Doc/fc_faq_04102022.pdf — confirms online
  filing at fcraonline.nic.in and mandatory NIL returns.
- PIB release (2020-09-16, PRID 1655000) confirming annual returns are uploaded
  on the FCRA portal and state-wise registered-association details are public.

## Real-data fetch attempt — 2026-09-23 (honest log)

Goal: pull real, public, bulk FCRA data (association lists / filed annual
returns) using only plain public HTTP fetches at a polite rate. No CAPTCHA
bypass, no login bypass, no paywall circumvention — those are hard standing
rules and were never attempted.

What was tried, in order:

1. `curl` (plain GET, research User-Agent, 30–40s timeouts) from the sandbox:
   - `https://fcraonline.nic.in/` → connection failed / empty reply (exit 52).
   - `https://fcraonline.nic.in/home/pdf_doc/associations.pdf` → same failure.
   - `http://fcraonline.nic.in/` → same failure.
   - Control: `https://example.com` and `http://example.com` → HTTP 200.
     The sandbox egress proxy works; the fcraonline.nic.in host specifically
     does not answer plain requests from this network (empty reply before any
     HTTP status).
2. `browser.open` (fetch-tool path) on `https://fcraonline.nic.in/` → returned
   an empty page (title "FCRA Online Services", no body text). The portal's
   landing page is a JS-driven shell; per-NGO and dashboard data flows through
   interactive POST-backed views, not plain static files.
3. `browser.open` on the known public FAQ PDF
   (`.../Home/PDF_Doc/fc_faq_04102022.pdf`) → **worked** (2,687 lines of text).
   This is a static document, not data, but it grounds the Form FC-4 schema.
4. `browser.open` on `https://fcraonline.nic.in/Home/PDF_Doc/associations.pdf`
   → tool failure, no recovery. Attempt stopped there per the no-retry rule.

**Outcome: 0 real rows obtained.** The portal's bulk data (registered-association
lists, filed annual returns) is served behind interactive/JS dashboard flows;
no clean static bulk file was reachable from this environment. Nothing was
scraped around the failure, and no access control was probed.

## What this means for the repo

- `data/real/` is intentionally empty. `data/sample/sample_fcra.json` (24
  illustrative rows) powers the UI and is labeled SAMPLE everywhere.
- Homepage stats are computed from the sample dataset and labeled "SAMPLE".
- The next step is a browser-based (human-supervised) pass over the MHA
  dashboard's public search to capture legitimately downloadable return
  lists, or an official data request — never a bypass.

## Scripts

- `scripts/fetch_fcra_public.py` — polite plain-GET fetcher for the portal's
  public static documents (NOT yet run successfully against the live portal;
  kept as the documented method for a future network where the host answers).
