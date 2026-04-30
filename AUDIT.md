# Scraper Audit — Live-Site Run

**Run date:** 2026-04-30
**Methodology:** each scraper module's HTTP entry points and a representative file URL were exercised against the live vendor site and graded against the verification checklist in [TASKS.md](TASKS.md). The `__main__.py` CLI was not used (it `sys.exit()`s on non-posix at [__main__.py:60](src/cobb_tracker/__main__.py#L60)); endpoints were exercised directly with `curl` and module logic was reproduced in Python against the saved responses. Selenium-driven NovusAgenda was checked statically only (requires Linux + `sudo docker run`).

## Verdict matrix

| Module | Vendor | HTTP OK | Listing parses | Coverage current | Date parse | PDF serves | Verdict |
|---|---|---|---|---|---|---|---|
| [civicplus.py](src/cobb_tracker/municipalities/civicplus.py) — Cobb | CivicClerk | ✅ 200 | ✅ | ✅ | ✅ | ✅ %PDF-1.4 | **OK** |
| [civicplus.py](src/cobb_tracker/municipalities/civicplus.py) — Kennesaw | CivicClerk | ✅ 200 | ✅ | ✅ | ✅ | ✅ (same backend) | **OK** |
| [acworth.py](src/cobb_tracker/municipalities/acworth.py) | IQM2 | ✅ 200 | ✅ | ❌ frozen at end of 2024 | ✅ | ✅ %PDF-1.7 (historic) | **Stale — missing all 2025/2026** |
| [marietta.py](src/cobb_tracker/municipalities/marietta.py) | CivicPlus AgendaCenter | ✅ 200 | ✅ | ✅ | ✅ | ✅ %PDF-1.6 | **OK** |
| [smyrna.py](src/cobb_tracker/municipalities/smyrna.py) | PrimeGov | ✅ 200 | ✅ | ✅ | ✅ | ✅ %PDF-1.7 | **OK** |
| [austell.py](src/cobb_tracker/municipalities/austell.py) | Sophicity → Municode (migrated) | ✅ 200 | ❌ on current page | ❌ | n/a | n/a | **Broken — vendor migrated** |
| [powdersprings.py](src/cobb_tracker/municipalities/powdersprings.py) | CivicPlus Archive Center | ⚠️ 301 to new domain | ✅ via follow | ✅ | ✅ | ✅ %PDF-1.7 (via redirect) | **Working but on borrowed time** |
| [novusagenda.py](src/cobb_tracker/municipalities/novusagenda.py) | NovusAgenda | ✅ 200 | not exercised (Selenium) | unknown | n/a | n/a | **Cannot run on Windows; static checks pass** |

---

## Per-module findings

### Cobb / Kennesaw — `civicplus.py` (CivicClerk)

- `GET https://cobbcoga.api.civicclerk.com/v1/Events/` → **HTTP 200**, `application/json` (OData), 56.8 KB.
- `GET https://kennesawga.api.civicclerk.com/v1/Events/` → **HTTP 200**, 59.2 KB.
- Both return 15 events on page 1 with a valid `@odata.nextLink` for pagination. Pagination loop in [civicplus.py:38-49](src/cobb_tracker/municipalities/civicplus.py#L38-L49) still applies.
- File-type counts on Cobb page 1: `Agenda: 14, Agenda Packet: 15, Minutes: 12`. Kennesaw page 1: `Agenda: 15, Agenda Packet: 15, Minutes: 14`. Module currently filters only `type == "Minutes"` ([civicplus.py:70](src/cobb_tracker/municipalities/civicplus.py#L70)) — confirming TASKS.md item to extend ingestion to agendas/packets is straightforward here (the data is already in `publishedFiles`).
- Spot-checked Cobb Minutes file (fileId=180) → `application/pdf`, magic `%PDF-1.4`, 1.13 MB.
- `categoryName` is populated on every event sampled; the `try/except` fallback to `"misc"` at [civicplus.py:58-63](src/cobb_tracker/municipalities/civicplus.py#L58-L63) was not triggered.
- **Note** — Sam mentioned Cobb is split across two storage backends. Only one host (`cobbcoga.api.civicclerk.com`) is wired into the module; if the second host carries records the first does not, those are silently missing. Catalogue task in TASKS.md is the right next step.

### Acworth — `acworth.py` (IQM2)

**This module is fetching nothing for 2025 or 2026.**

- `GET https://acworthcityga.iqm2.com//api/Agency/StartupData` → **HTTP 200** (the doubled slash is harmless but should be cleaned up at [acworth.py:11-15](src/cobb_tracker/municipalities/acworth.py#L11-L15)).
- `MeetingRanges` returned: `[2024, 2023, …, 2006]` — **no 2025 entry, no 2026 entry**. Plus the `Recent` bucket (ID=1) which the scraper deliberately skips at [acworth.py:46-48](src/cobb_tracker/municipalities/acworth.py#L46-L48).
- `GET /api/Meeting?Range=2025&Group=70/` → **HTTP 200** with body `[]`. Same for `Range=1`. So 2025/2026 records are not hidden under "Recent" either — IQM2 simply has no current Acworth content.
- 2024 still works: `Range=2024&Group=70` returns 103 meetings with 62 Minutes attached. Spot-checked one PDF (Type=15&ID=2115) → `application/pdf`, `%PDF-1.7`, 124 KB.
- **What this means.** The IQM2 platform appears to be the abandoned half of the platform-cutover Sam flagged. Historical pulls 2006–2024 are intact; ongoing scrapes produce 0 new docs per run. This is exactly the kind of silent failure the audit was meant to catch.
- 12 meeting groups exist; only one (`Group=70`) was probed. The empty-2025 finding is unlikely to differ across groups but isn't proven for all 12.

### Marietta — `marietta.py` (CivicPlus AgendaCenter)

- `GET https://www.mariettaga.gov/AgendaCenter` → **HTTP 200**, 316 KB.
- 8 `<div class="listing listingCollapse noHeader">` containers found (Board of Lights and Water, Board of Zoning Appeals, City Council, …). Each has the expected `<h2 tabindex="0">`, `<table summary="List of Agendas">` with a digit-suffixed id, and `<ul class="years">`.
- Year list on each container: `['2026', '2025', '2024', 'View More', '2023', '2022', '2021', '2020']`. The non-numeric `View More` entry is correctly filtered by `is_year` at [marietta.py:159-169](src/cobb_tracker/municipalities/marietta.py#L159-L169).
- `POST /AgendaCenter/UpdateCategoryList` with `{year:'2024', catID:'7'}` → **HTTP 200**, 108 KB, 135 rows (`tr.catAgendaRow`). Every row has both a meeting title and a minutes link.
- 2026 POST returns rows but `minutes_href` is `None` for them (minutes not yet published). Module handles this correctly via `if minutes_link:` at [marietta.py:127](src/cobb_tracker/municipalities/marietta.py#L127).
- Date parsing from filename slice (`_12192024-2636` → `2024-12-19`) at [marietta.py:54-60](src/cobb_tracker/municipalities/marietta.py#L54-L60) still produces correct dates against the live data.
- Spot-checked PDF: `application/pdf`, `%PDF-1.6`, 259 KB.

### Smyrna — `smyrna.py` (PrimeGov)

- `GET https://smyrnaga.primegov.com/api/v2/PublicPortal/ListArchivedMeetings?year=2026` → **HTTP 200**, JSON array of 47 events.
- Document templates seen across 2026: `Action Summary`, `Agenda`, `HTML Agenda`, `Minutes`, `Notice of Cancellation`, `Packet`. **27 Minutes docs already published for 2026.**
- This directly confirms the TASKS.md item — the same JSON exposes Agenda, Packet, and HTML Agenda alongside Minutes, so dropping the `templateName == "Minutes"` filter at [smyrna.py:65](src/cobb_tracker/municipalities/smyrna.py#L65) and keying off the template name as the doc-type is a one-line change to multi-doc ingestion.
- Date parse `"Jan 05, 2026"` → `2026-01-05` works.
- Title-cleanup regex chain at [smyrna.py:46-53](src/cobb_tracker/municipalities/smyrna.py#L46-L53) was applied to a sample title `'Planning and Zoning Meeting - A. Max Bacon City Hall - Council Chambers'` and reduced cleanly without nuking the entire title.
- Spot-checked Minutes URL (templateId=7677) → `application/pdf`, `%PDF-1.7`, 159 KB. **The CompiledDocument endpoint 302-redirects to a temporary signed Azure Blob URL** (`pgwest.blob.core.windows.net/...?sv=…&sig=…&st=2026-04-29T13:37:10Z&se=2026-05-01T13:37:10Z`). The signed URL is good for ~2 days from issue. `requests.Session` follows the redirect inline so this is fine — but we should never persist the resolved blob URL anywhere (the signature expires).

### Austell — `austell.py` (Sophicity → Municode Meetings, **migrated**)

**Broken: vendor migration is the root cause.**

- `GET https://www.austellga.gov/AgendasandMinutes.aspx` → **HTTP 200** but the page no longer contains a `Minutes` `<h3>`. The `mcms_RendererContentDetail` div is present but its only useful content is a button-link reading **"Click here to view CURRENT Agenda and Minutes"** pointing at `https://austell-ga.municodemeetings.com/`. Austell migrated to Municode Meetings.
- The `Minutes` h3 detection at [austell.py:42-45](src/cobb_tracker/municipalities/austell.py#L42-L45) returns `[]` for the current page → loop over `minutes_divs` is a no-op → no current minutes scraped. No exception, no log line, just a silent zero.
- The "past" page (`PastAgendasandMinutes.aspx`) still has the legacy structure (15 alternating `Agendas` / `Minutes` h3 sections plus 6 trailing `Minutes`-only blocks). So the scraper continues to pull historical data, but everything new lives on Municode.
- `GET https://austell-ga.municodemeetings.com/` → **HTTP 200**, 70 KB HTML — the new site is reachable but unsupported by the codebase.
- Sophicity is essentially dead for Austell going forward. Either add a Municode Meetings module (new vendor: Municode lists this product publicly) or wait until the broader Paperless rewrite and start fresh there.

### Powder Springs — `powdersprings.py` (CivicPlus Archive Center, **domain migrated**)

**Working today only because `requests` follows 301s.**

- `GET https://cityofpowdersprings.org/Archive.aspx` → **HTTP 200** after **2 redirects** to `https://www.powderspringsga.gov/Archive.aspx`. The city has rebranded its primary domain from `cityofpowdersprings.org` to `powderspringsga.gov`.
- All hardcoded constants in [powdersprings.py:27-30](src/cobb_tracker/municipalities/powdersprings.py#L27-L30) point at the legacy domain. `requests.Session.get` follows 301s by default, so the parser keeps working.
- Archive Details table is still present with 15 `<select id="amidDDN##">` and matching `<label for=…>` pairs — group extraction at [powdersprings.py:67-72](src/cobb_tracker/municipalities/powdersprings.py#L67-L72) still works.
- `archive` spans on inner pages still carry date-bearing names (`'April 6, 2026  '`, `'March 16, 2026  '`). `get_year` regex matches the `MMM DD, YYYY` form on these — date-fallback path is not triggered for current data.
- `GET https://cityofpowdersprings.org/ArchiveCenter/ViewFile/Item/4709` → 301 → `https://www.powderspringsga.gov/...` → **HTTP 200**, `application/pdf`, `%PDF-1.7`, 132 KB.
- **Risk:** the city can drop the legacy redirect at any time. Move all four constants to `https://www.powderspringsga.gov/` now.

### NovusAgenda Kennesaw — `novusagenda.py` (legacy)

- `GET https://kennesaw.novusagenda.com/agendapublic` → **HTTP 200** after 1 redirect (trailing-slash normalization), 84.5 KB. Title `<title>NovusAGENDA</title>`.
- Expected element IDs (`ddlDateRange`, `SearchAgendasMeetings`, `radGridMeetings`) are all present in the static HTML.
- **Could not actually run.** Module hard-codes `sudo docker run …/selenium/standalone-chrome` ([novusagenda.py:65-105](src/cobb_tracker/municipalities/novusagenda.py#L65-L105)) and exits on Windows. So nothing past page-load was exercised this run.
- TASKS.md already flags this module as possibly obsolete (Kennesaw migrated to CivicClerk). The CivicClerk Kennesaw run above pulled 14 Minutes on page 1 alone, so the live source is fine without it. Decision needed: delete or rewrite for the era this can still cover.

---

## Cross-cutting findings

1. **Silent zero is the most common failure mode.** Acworth (post-2024) and Austell (current page) both produce empty result sets without raising or logging anything. The audit checklist's "Empty result set is *real*, not a parser miss" criterion catches both. Worth wiring a per-run sanity check ("0 new docs from a jurisdiction that historically averaged N/month → log a warning") before the Paperless rewrite, since regressions only get more expensive once we're shipping into a real document store.
2. **Vendor migrations are the leading cause of breakage.** Austell (Sophicity→Municode), Powder Springs (legacy domain → new domain), Acworth (IQM2 → ?). The domain catalogue task in TASKS.md A is the highest-leverage thing to do next.
3. **Multi-doc data is already on the wire for 3 of 5 working modules.** CivicClerk (Cobb/Kennesaw) and PrimeGov (Smyrna) already return Agenda/Packet/Minutes side-by-side; the scrapers throw away two thirds of it. Marietta would also benefit but requires a different selector path. Smyrna is the cheapest to extend.
4. **Random-key date fallback was not exercised** in any working module on this run. Powder Springs current-data dates all matched the regex on the first pass; no spell-correct or per-page deep-dive was triggered. Confirms TASKS.md note that the fallback only fires on legacy oddities.
5. **All sampled file URLs returned real PDFs.** Five spot-checks across four vendors: Content-Type was always `application/pdf` and the body started with `%PDF-1.x`. No HTML-with-200 silent failures observed today.
6. **Acworth's BASE_URL has a stray `//`**. Cosmetic but worth a one-line fix at [acworth.py:11-15](src/cobb_tracker/municipalities/acworth.py#L11-L15).

## Recommended actions (delta vs. TASKS.md)

These are the items the audit *concretely escalates* — not new tasks, just sharper priority:

1. **Acworth migration** (new) — IQM2 is no longer the source of truth. Identify which of the 4 active Acworth domains hosts current minutes, add a module for it. Until then, the scraper produces 0 new Acworth docs per run.
2. **Austell migration** (new) — Build a Municode Meetings adapter (new vendor, currently unrepresented in the codebase) targeting `austell-ga.municodemeetings.com`. The current scraper covers only pre-migration history.
3. **Powder Springs domain swap** (small, do now) — replace the four constants in [powdersprings.py:27-30](src/cobb_tracker/municipalities/powdersprings.py#L27-L30) with `https://www.powderspringsga.gov/`. One-line risk reduction.
4. **Smyrna multi-doc** (smallest unlock for the agendas/packets goal) — drop the `templateName == "Minutes"` filter at [smyrna.py:65](src/cobb_tracker/municipalities/smyrna.py#L65) and key off `templateName` as the doc-type tag. Already-flagged in TASKS.md; this audit confirms the data is there for 2026.
5. **Sanity-check guardrail** — log a warning when a module that historically returned >0 docs returns 0. Would have surfaced Acworth and Austell automatically.

## Raw artefacts

Saved fetch responses are in `audit-tmp/` (gitignored — not committed). Each scraper's main listing endpoint plus one PDF spot-check is captured.
