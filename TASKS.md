# Cobb Tracker — Remaining Work

## Direction shift

The repo's role is changing:

- **cobb-tracker** = scraper + metadata pipeline only.
- **Paperless-ngx** = document store, OCR, FTS, tagging.
- **New thin frontend** = citizen-facing search UI on top of Paperless.

Today the repo only ingests **minutes**, OCRs them with Tesseract into SQLite, and serves the result with Datasette. The OCR/SQLite/Datasette layer goes away once Paperless is in place. Scope of ingestion expands to **agendas + agenda packets + minutes** for Cobb County and every city in it.

## Scraper — current state per module

Last live-site audit: **2026-04-30** ([AUDIT.md](AUDIT.md)).

| Module | Vendor | Status | Notes |
|---|---|---|---|
| [civicplus.py](src/cobb_tracker/municipalities/civicplus.py) (Cobb, Kennesaw) | **CivicClerk** (misnamed in code) | OK (verified 2026-04-30) | Cobb is split across two storage backends per the domain migration — only `cobbcoga.api.civicclerk.com` was probed; the other backend is still uncatalogued. CivicClerk's `publishedFiles` already exposes Agenda + Agenda Packet alongside Minutes — module currently throws those away. |
| [acworth.py](src/cobb_tracker/municipalities/acworth.py) | **IQM2** | **Broken — 0 new docs since 2024-12-31** | IQM2 `MeetingRanges` ends at 2024; `Range=2025` and the `Recent` bucket both return `[]`. Historic 2006–2024 still pulls correctly. Acworth has 4 active domains and 2 platform cutover dates — IQM2 is the abandoned half. Module needs to be repointed (or replaced) to whichever platform now hosts current minutes. |
| [marietta.py](src/cobb_tracker/municipalities/marietta.py) | **CivicPlus AgendaCenter** | OK (verified 2026-04-30) | Year-by-year POST against `UpdateCategoryList`. 8 containers, `is_year` correctly filters the `View More` entry, 2024 City Council pulls 135 rows all with minutes URLs. |
| [smyrna.py](src/cobb_tracker/municipalities/smyrna.py) | **PrimeGov** | OK (verified 2026-04-30) | Heavy regex cleanup of clerk-authored titles. Smyrna's full 2013→present history is in PrimeGov with agendas + minutes attached; the 2013 floor at [smyrna.py:32](src/cobb_tracker/municipalities/smyrna.py#L32) matches the actual data edge (year=2012 returns an empty array). The old Legistar deployment at `webapi.legistar.com/v1/SmyrnaCity/` is abandoned (last event 2022-12-19) — superseded by PrimeGov, don't scrape it. PrimeGov serves PDFs via short-lived signed Azure Blob URLs (~2 day TTL) — never persist the resolved blob URL. |
| [austell.py](src/cobb_tracker/municipalities/austell.py) | **Sophicity → Municode Meetings (migrated)** | **Broken — vendor migration** | The current page (`AgendasandMinutes.aspx`) no longer contains a `Minutes` `<h3>` — it now just links out to `https://austell-ga.municodemeetings.com/`. Parser silently returns `[]` for current data. Past page still has the legacy structure, so historical pulls keep working. Need a Municode Meetings adapter (new vendor, currently unrepresented). |
| [powdersprings.py](src/cobb_tracker/municipalities/powdersprings.py) | **CivicPlus Archive Center** | Working via 301 — domain migrated | `cityofpowdersprings.org` 301-redirects to `www.powderspringsga.gov`; module's hardcoded constants still point at the legacy domain and are working only because `requests.Session` follows redirects. Selectors and date parsing all still match. The brittle date-regex + spell-correct fallback was not exercised against current data on the audit run. |
| [novusagenda.py](src/cobb_tracker/municipalities/novusagenda.py) (Kennesaw legacy) | **NovusAgenda** | **Archive-only — frozen at 2023-04-24** | Selenium path now portable to Windows ([novusagenda.py:87](src/cobb_tracker/municipalities/novusagenda.py#L87) + signal handler at [novusagenda.py:45-53](src/cobb_tracker/municipalities/novusagenda.py#L45-L53)). Live verification 2026-04-30: 36 pages, 320 historical minutes URLs, PDFs serve correctly. **Most recent entry 2023-04-24** — site has been dead for new content for 2+ years. CivicClerk Kennesaw covers everything from the cutover forward, so this module has no ongoing role. Only remaining purpose is a one-time historical backfill of the 320 pre-2023 PDFs. |
| (none) | **Municode Meetings** | Missing | New vendor surfaced by Austell's migration. Confirm host (`austell-ga.municodemeetings.com`) and any other Cobb-county jurisdictions on the same platform. |
| (none) | **Legistar** | Missing | Sam listed it as one of five active vendors. Smyrna had a Legistar deployment but migrated to PrimeGov with all records intact — Smyrna is *not* the target. Which jurisdiction Sam meant is still TBD. |
| (none) | **Laserfische WebLink** | Documented gap | Needs session-walking pseudo-filesystem. Only confirmed in-scope use is pre-2013 Smyrna, and only if that era is actually in scope. |
| (none) | **Mableton** | Missing | New city (incorporated 2022); not yet scraped. |

## Tasks

### A. Scraper audit & repair

- [x] Run each module against the live site, record what still works (HTTP errors, parser breakage, empty result sets). Done 2026-04-30 — see [AUDIT.md](AUDIT.md).
- [ ] **Repoint Acworth.** IQM2 froze at end of 2024 (0 new docs in 2025/2026). Identify which of Acworth's 4 active domains hosts current minutes and either retarget [acworth.py](src/cobb_tracker/municipalities/acworth.py) or write a new module. Until then, Acworth contributes nothing to ongoing scrapes.
- [ ] **Add a Municode Meetings adapter for Austell.** Sophicity is dead for current Austell content; new vendor host is `https://austell-ga.municodemeetings.com/`. Existing [austell.py](src/cobb_tracker/municipalities/austell.py) only covers pre-migration history.
- [ ] **Update Powder Springs constants** at [powdersprings.py:27-30](src/cobb_tracker/municipalities/powdersprings.py#L27-L30) from `https://cityofpowdersprings.org/` to `https://www.powderspringsga.gov/`. One-line risk reduction — works today only because `requests` follows the legacy 301.
- [ ] Catalogue the actual vendor + URL set per jurisdiction — especially Acworth's 4 domains and Cobb's 2 storage backends. Audit only probed one Cobb backend (`cobbcoga.api.civicclerk.com`); the second is still uncatalogued.
- [ ] Rename [civicplus.py](src/cobb_tracker/municipalities/civicplus.py) → `civicclerk.py`. The `CivicPlus` class talks to the CivicClerk API, not the AgendaCenter platform Marietta uses. The naming drift is a future bug magnet.
- [ ] Extend every scraper to pull **agendas** and **agenda packets**, not just minutes. Today [file_ops.py:56](src/cobb_tracker/file_ops.py#L56) hard-codes `{date}-{file_type}.pdf` and every scraper sets `file_type = "minutes"`; [pdf_parse.py:125](src/cobb_tracker/pdf_parse.py#L125) strips `-minutes.pdf` to derive the date — both assumptions need to go. **Smyrna is the cheapest unlock** (audit-confirmed): every PrimeGov event already exposes Agenda + Packet + HTML Agenda + Minutes in `documentList`; just stop filtering on `templateName == "Minutes"` at [smyrna.py:65](src/cobb_tracker/municipalities/smyrna.py#L65) and key off the template name as the doc-type. CivicClerk (Cobb/Kennesaw) similarly returns `Agenda` / `Agenda Packet` / `Minutes` in the same `publishedFiles` array.
- [ ] **Sanity-check guardrail.** Log a warning when a module that historically returned >0 docs returns 0 in a run. Acworth and Austell both failed silently this audit; this would have caught both automatically.
- [ ] Clean up the doubled `//` in [acworth.py:11-15](src/cobb_tracker/municipalities/acworth.py#L11-L15) (cosmetic — request still works).
- [ ] Add **Mableton** (vendor TBD).
- [ ] **Retire NovusAgenda Kennesaw scraping.** Verified 2026-04-30: site is frozen at 2023-04-24, CivicClerk has been the live source since. Plan: (a) one-time historical backfill of the 320 pre-2023 PDFs the module enumerates, then (b) delete [novusagenda.py](src/cobb_tracker/municipalities/novusagenda.py) and drop the Selenium + Docker runtime dependency from the project. Until backfill happens, the Windows-portable scrape ([novusagenda.py:87](src/cobb_tracker/municipalities/novusagenda.py#L87)) is what runs it.
- [ ] Add **Laserfische WebLink** support if any in-scope jurisdiction uses it.
- [ ] Add **Legistar** support for whichever jurisdiction Sam noted.
- [ ] Replace the random `unknownNNN` date fallback in [string_ops.py:13](src/cobb_tracker/string_ops.py#L13) with a "needs review" queue — silent random keys are how docs get lost.
- [ ] Standardize the `file_urls` dict shape across scrapers (today each module hand-rolls it).

### B. Pipeline rewrite for Paperless-ngx

- [ ] Replace the SQLite + Tesseract sink with a **Paperless-ngx push** via `POST /api/documents/post_document/`.
- [ ] Map cobb-tracker metadata → Paperless concepts:
  - `municipality` → Correspondent
  - `body` / `meeting_name` → Tag
  - `file_type` (agenda / packet / minutes) → Document Type
  - `date` → `created`
  - source URL → custom field (permalink back to source site)
- [ ] Keep the existing SHA-256 checksum behavior in [file_ops.py:82](src/cobb_tracker/file_ops.py#L82) for client-side dedupe; resolve duplicates against Paperless before POSTing so its rejection logs stay clean.
- [ ] Handle the **mixed-format agenda packets** Sam flagged. Options: pre-split the packet, normalize embedded DOCX/PPTX to PDF via headless LibreOffice, then submit either as one merged PDF with bookmarks or as separate Paperless docs in a group. Pick one.
- [ ] Delete the [pdf_parse.py](src/cobb_tracker/pdf_parse.py) Tesseract/SQLite path once Paperless is the OCR layer. Keep [file_ops.py](src/cobb_tracker/file_ops.py) for download + checksum, but route output to either a Paperless **consume** folder or the API directly (pick one — don't run both).
- [ ] Drop the `os.name != "posix"` guard in [__main__.py:60](src/cobb_tracker/__main__.py#L60) so contributors on Windows/macOS can run scrapers.

### C. Citizen-facing frontend

- [ ] Spec v1 UX. Assumed baseline: single search box → results list with snippet + jurisdiction + body + date + link to source PDF, plus facets for municipality / body / document type / date range.
- [ ] Backend choice: call the Paperless API directly from a thin SvelteKit/Next.js app, **or** mirror Paperless content into a dedicated search index (Meilisearch / Typesense). Direct API is simpler; a dedicated index is faster and hides the Paperless admin surface from the public.
- [ ] Stable permalink scheme (e.g. `/doc/<municipality>/<body>/<date>`).
- [ ] Public read with no login. Confirm Paperless can serve read-only documents publicly without exposing the admin UI (or terminate that at the frontend).

### D. Deployment & ops (k3s homelab + Hetzner)

- [ ] Helm chart / manifests for Paperless-ngx + Postgres + Redis + Tika + Gotenberg.
- [ ] Cobb-tracker scrapers as one `CronJob` per jurisdiction (so a single broken scraper doesn't block the others).
- [ ] PVCs for the consume folder and Paperless media.
- [ ] Backup strategy (Paperless DB + media) — Hetzner as offsite target.
- [ ] Failure notifications somewhere visible (Healthchecks.io / ntfy). The previous deployment "went offline a while" with no one noticing.
- [ ] [.github/workflows/build.yml](.github/workflows/build.yml) only builds on tag push and uses deprecated actions (`upload-artifact@v1`, `Gr1N/setup-poetry@v8`). Add scraper smoke tests + lint on PR; refresh action versions.

### E. Code quality / tech debt

- [ ] **No tests exist.** Add HTML-fixture-based unit tests per scraper so vendor markup changes get caught at PR time, not months later in prod.
- [ ] CLI logic in [__main__.py:111-132](src/cobb_tracker/__main__.py#L111-L132) is incoherent: `--pull-all-cities` is `store_true`, so the `is None` checks are dead code, and "no flag = scrape everything" happens via the trailing `if args.municipality is None: choose_muni("all", config)`. Either intentional and undocumented, or a bug.
- [ ] [pdf_parse.py:128](src/cobb_tracker/pdf_parse.py#L128) builds SQL via f-string. Low risk today since input is a hex digest, but replace with a parameterized query.
- [ ] [file_ops.py:62](src/cobb_tracker/file_ops.py#L62) uses module-level `requests.get` instead of the pooled `self.session` it was passed.
- [ ] `os.sched_getaffinity(0)` in [pdf_parse.py:33](src/cobb_tracker/pdf_parse.py#L33) is Linux-only — breaks macOS even today. Moot if E.B retires this file, but worth noting.

## Open questions

These block sections B and C — would like answers before sinking time into them.

1. ~~**Existing corpus.** Is there a backup of the database/files from Sam's last working deployment? If yes, we ingest that into Paperless rather than re-scraping years of history.~~ **Resolved 2026-04-30:** Sam has a backup and plans to ingest it into Paperless. Scraper still needs to cover the 2025–2026 gap (which lines up with the Acworth/Austell breakage windows in the audit).
2. **Mableton in scope?** And which platform is it on?
3. **Legistar / Laserfische** — which jurisdictions specifically? (Confirmed *not* Smyrna: its Legistar history was migrated into PrimeGov, and Laserfiche only matters for pre-2013 Smyrna if that era is in scope.)
4. **Agenda packets.** Pre-split on our side, or preserve the original composite in Paperless and accept the OCR limitations?
5. **Frontend scope for v1.** Just search + filters + results? Or also saved searches / email alerts / RSS for keywords (e.g. someone subscribes to "cobblinc")?
6. **Auth model.** Fully public read, no login? Or gated for early users?
7. **Hosting split.** Frontend on Hetzner with Paperless + scrapers in the homelab over a tunnel? Or all in Hetzner? Or all in homelab with Hetzner as failover only?
8. **Parallel raw-text store.** Replace SQLite/Datasette entirely with Paperless, or keep cobb-tracker's DB as a parallel raw-text store for the kind of bulk-text queries Paperless's UI is bad at?
