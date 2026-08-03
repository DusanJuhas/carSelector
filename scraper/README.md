# carSelector — web scraping module

Local working copy for developing the web scraping module for the
[carSelector](https://github.com/DusanJuhas/carSelector) project (AI
Assisted Car Selection Tool). The module (`scraper/`) downloads vehicle
price lists directly from manufacturer websites, extracts variants/
prices/equipment from the PDFs, and stores them in a database that the
rest of the application (car selection/filtering) will query.

## Why local and not directly in the main GitHub repo

The rest of the team works in the main repo (frontend, backend, AI
layer). The web scraping module is developed and verified separately so
it doesn't break things for others through work-in-progress PRs. Once
the module is working and verified on real data, it will be moved into
the main repo:

- `scraper/` → new folder in the root of `carSelector` (production code)
- `doc/arch/webScraping/` → merged with the existing folder of the same
  name in the main repo (architecture and docs only, no code)

## Current data coverage

| Brand | Model | Powertrain |
|---|---|---|
| Škoda | Fabia, Scala, Kamiq, Octavia, Karoq, Kodiaq, Superb | ICE |
| Škoda | Enyaq, Elroq, Epiq, Peaq | EV |
| Volkswagen | Golf, Golf Variant, Passat, Polo, T-Cross, T-Roc, Taigo, Tayron, Tiguan, Touran | ICE / MHEV / PHEV |
| Volkswagen | ID.3 Neo, ID.4, ID.7, ID.7 Tourer, ID. Polo | EV |

Every variant has a price, a trim level, and a link back to the page/
exact text in the source PDF (`raw_text`), so it can always be verified
against the source. Škoda additionally includes optional equipment (the
"Samostatné prvky výbavy" / standalone equipment items page — other
equipment formats, VW equipment, and other OEMs are listed under
[Status and next steps](#status-and-next-steps)).

## Installation

Requires **Python 3.10+**.

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r scraper/requirements.txt
```

The dependencies in `scraper/requirements.txt` are what's actually used
today (requests, beautifulsoup4, pdfplumber, sqlalchemy, pyyaml, click,
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
carSelector/
├── scraper/                    # production code — will move to the root of the main repo
│   ├── config/                  # OEM source registry, sources.yaml
│   ├── sources/                 # SourceRegistry — loads the registry
│   ├── downloaders/             # PdfDownloader — downloads PDFs
│   ├── monitors/
│   │   ├── discovery/            # BaseDiscoverer + per-brand discoverers
│   │   └── source_monitor.py     # SourceMonitor — orchestrates finding new documents
│   ├── parsers/                 # BaseParser + per-brand/powertrain parsers (plugin architecture)
│   ├── normalization/           # EquipmentNormalizer — unifies equipment names across brands
│   ├── database/                # SQLAlchemy models + repositories (Document/Variant/Equipment)
│   ├── verification/            # review_cli.py — manually verify extracted data against the PDF
│   ├── storage/                 # downloaded PDFs + SQLite DB (gitignored, except .gitkeep)
│   ├── tests/                   # tests + PDF fixtures
│   ├── tools/                   # datasette_metadata.json — data browsing config
│   └── main.py                  # ScraperPipeline — entry point (python -m scraper.main)
└── doc/arch/webScraping/        # architecture and decisions — will move to the main repo
    ├── Car_Price_List_Architecture.md   # target architecture (full tech stack, all OEMs)
    └── IMPLEMENTATION_PLAN.md            # phased plan (vertical slice → generalization)
```

Adding a new brand/model = a new file in `parsers/` and
`monitors/discovery/` + an entry in both registries
(`parsers/registry.py`, `monitors/discovery/registry.py`) + an entry in
`sources.yaml` — without touching existing code for other brands.

## Status and next steps

Done: OOP architecture (class + plugin registry for both parsers and
discoverers), Škoda and VW complete (both ICE and EV), optional
equipment for Škoda (one of three formats — "Samostatné prvky výbavy" /
standalone equipment items).

Remaining: Škoda "Pakety" (packages) and per-trim standard equipment
(the other two equipment formats), VW equipment (different format),
Toyota/Hyundai/Kia. Details and the reasoning for scaling one piece at a
time (vertical slice, verify on real data, then generalize) are in
`doc/arch/webScraping/IMPLEMENTATION_PLAN.md`.
