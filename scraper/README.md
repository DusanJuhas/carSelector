# DriveWise AI – scraper

Standalone Python service that downloads vehicle price lists directly from manufacturer websites,
extracts variants/prices/equipment from the PDFs, and stores them in its own database. See
`doc/prompt/CLAUDE.md` for repo-wide conventions.

**For architecture, data coverage, and status/next-steps, see
[`doc/arch/webScraping/`](../doc/arch/webScraping/)** — this README only covers running the module
locally. `Car_Price_List_Architecture.md` there is the target design; `IMPLEMENTATION_PLAN.md` has
the phased rollout plan plus the current brand/model coverage table and remaining work, kept up to
date as brands are added.

Note this schema is separate from the backend's catalog database (`backend/app/models/`) — there
is currently no import step from `scraper/storage/scraper.db` into it; see
`.claude/skills/drivewise-data-model/SKILL.md` for that boundary.

## Installation

Requires **Python 3.10+**. Dependencies are consolidated in one `requirements.txt`/
`requirements-dev.txt` pair at the **repo root** (shared with `backend/`, which is a separate
FastAPI service — this file being shared doesn't couple them), so run this from the repo root:

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt   # requirements.txt + pytest, for running scraper/tests/
```

The scraper-relevant dependencies in `requirements.txt` are what's actually
used today (requests, beautifulsoup4, pdfplumber, sqlalchemy, pyyaml, click,
pytest) — not the full target tech stack from the architecture doc (see
`doc/arch/webScraping/Car_Price_List_Architecture.md`), which also plans
for Playwright/Camelot/PyMuPDF/Postgres/FastAPI in later phases.

## Running

```bash
python -m scraper.main
```

For every active source (`scraper/config/sources.yaml`, `active: true`)
it checks for new/changed price lists, downloads them into
`scraper/storage/<brand>/`, parses them, and stores the result in a
local SQLite database at `scraper/storage/scraper.db` (can be switched
via the `SCRAPER_DATABASE_URL` environment variable, e.g. to Postgres).

## Tests

```bash
pytest scraper/tests/ -v
```

All tests run against real PDF fixture files (`scraper/tests/fixtures/`)
with prices/values transcribed by hand directly from the PDF — not
derived from the parser — so a test verifies extraction against the
source, not against itself.

## Browsing the collected data

**Datasette** (recommended, free, no code) — a web UI with filters/facets
over the whole database:

```bash
pip install datasette
datasette scraper/storage/scraper.db \
  --metadata scraper/tools/datasette_metadata.json \
  --port 8001
```

Open `http://127.0.0.1:8001` — the `variant` table has facets (filters)
preconfigured for `brand`/`model`/`trim`/`powertrain`, the `document`
table for `source_brand`, the `equipment_assignment` table for
`availability`, all sorted with the newest records first.

Other options:
- **Raw SQL:** `sqlite3 scraper/storage/scraper.db`
- **GUI app:** [DB Browser for SQLite](https://sqlitebrowser.org/) (free) — open `scraper/storage/scraper.db`
- **Verify against the PDF:** `python -m scraper.verification.review_cli --document-id <ID>` prints every variant together with the exact `raw_text` it was extracted from

## Structure

```text
scraper/
├── config/                  # OEM source registry, sources.yaml
├── sources/                 # SourceRegistry — loads the registry
├── downloaders/             # PdfDownloader — downloads PDFs
├── monitors/
│   ├── discovery/            # BaseDiscoverer + per-brand discoverers
│   └── source_monitor.py     # SourceMonitor — orchestrates finding new documents
├── parsers/                 # BaseParser + per-brand/powertrain parsers (plugin architecture)
├── normalization/           # EquipmentNormalizer — unifies equipment names across brands
├── database/                # SQLAlchemy models + repositories (Document/Variant/Equipment)
├── verification/            # review_cli.py — manually verify extracted data against the PDF
├── storage/                 # downloaded PDFs + SQLite DB (gitignored, except .gitkeep)
├── tests/                   # tests + PDF fixtures
├── tools/                   # datasette_metadata.json — data browsing config
└── main.py                  # ScraperPipeline — entry point (python -m scraper.main)
```

Adding a new brand/model = a new file in `parsers/` and
`monitors/discovery/` + an entry in both registries
(`parsers/registry.py`, `monitors/discovery/registry.py`) + an entry in
`sources.yaml` — without touching existing code for other brands.
