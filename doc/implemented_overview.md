# DriveWise AI — Implementation Overview

A car-selection assistant: users describe how they'll use a car in a chat, an AI layer turns that
into structured requirements, a deterministic engine filters/ranks the real catalog, and the AI
explains each result. A second, independent service scrapes manufacturer price lists to grow that
catalog. This doc is a snapshot of what's actually built, not the target architecture — see
`doc/arch/` and each service's own README for design docs and open items.

## Architecture

Three independent services, one shared SQLite dev database for backend + scraper (`storage/`):

- **`backend/`** — FastAPI REST API: catalog data, the recommendation engine, and the AI
  conversation flow.
- **`frontend/`** — React SPA that talks to the backend over HTTP.
- **`scraper/`** — standalone pipeline that downloads OEM PDF price lists and extracts
  vehicles/prices/equipment into its own database. Not wired to the backend automatically; a script
  imports its data into the backend's catalog on demand.

## Tech stack

| Layer | Stack |
|---|---|
| Backend | Python, FastAPI, SQLAlchemy 2.x, Alembic, Pydantic v2, SQLite (dev) / PostgreSQL (target, dual-dialect schema), Anthropic Claude API (`anthropic` SDK) |
| Frontend | React 19, TypeScript, Vite, Tailwind CSS v4, Zustand (state), axios, react-i18next, Vitest + Testing Library |
| Scraper | Python, requests, BeautifulSoup, pdfplumber, SQLAlchemy, Click, PyYAML |

## Implemented features

**Catalog (backend + frontend)**
- `GET /api/brands`, `GET /api/models/{id}`, `GET /api/vehicles` (paginated, sortable by
  price/alpha), `GET /api/vehicles/{configuration_id}` (full detail), `GET /api/vehicles/compare`.
- Schema: brand → model → {trims, powertrains, colors, option items, source documents} →
  configuration → {prices, configuration colors, option availability}. Business rules enforced at
  the DB level (unique "current" price per market, valid-date ordering, etc.) — see
  [`doc/db/implemented_overview` diagram](db/drivewise-schema.png) if present, or `doc/db/`.
- Currently seeded with one hand-verified vehicle (Mazda CX-5) plus real scraper-imported data
  (`scripts/import_scraper_data.py`).

**AI-driven conversation (backend `app/ai/`, `app/services/conversation.py`)**
- `POST /api/conversations` starts a chat; `POST /api/conversations/{id}/messages` sends a turn.
- Flow per turn: Claude extracts `StructuredRequirements` from free text → a deterministic
  `RecommendationEngine` filters the catalog on hard constraints (body type, budget, fuel type) and
  scores the rest (drivetrain match, priority match, budget headroom) → Claude generates a
  per-vehicle explanation. The AI never queries or ranks the database directly.
- Conversation state is in-memory only (no persistence yet, no multi-process support).
- Degrades to `503 ai_not_configured` if `ANTHROPIC_API_KEY` isn't set; catalog browsing still
  works without it.

**Frontend UI (`frontend/src/`)**
- Two-column chat layout: conversation on the left, results grid on the right.
- **Browsing mode** (default, before the AI has narrowed anything): paginated catalog with
  server-side sort (price asc/desc, alphabetical) or client-side drag-to-reorder ("custom").
- **Narrowed mode** (after the AI returns matches): shortlist with match scores/flags, sorted
  client-side.
- Requirements drawer showing the requirements extracted so far; vehicle detail modal; car cards.
- All user-facing copy is Czech (`i18n/locales/cs.json`); `en.json` exists but Czech is the
  authored/verified language per project convention.
- Component tests with Vitest + Testing Library for the major components/hooks.

**Scraper (`scraper/`)**
- Per-brand discoverer + parser plugins find and download PDF price lists
  (`scraper/config/sources.yaml` lists active sources), extract variants/prices/equipment, and
  normalize equipment names across brands.
- Stores into its own SQLite DB (`storage/scraper.db`), browsable via Datasette or any SQLite
  client; `scraper/verification/review_cli.py` cross-checks extracted data against the source PDF.
- Known gap: imported vehicles have no `option_items`/`option_availability` rows (no surcharge data
  in the source PDFs yet), so equipment lists are empty for scraper-imported cars.

## Running locally

**Backend** (from repo root):
```bash
python -m venv .venv
.venv\Scripts\activate            # Windows; source .venv/bin/activate elsewhere
pip install -r requirements-dev.txt
cd backend
alembic upgrade head               # creates storage/drivewise.db + schema
python -m app.db.seed              # seeds one hand-verified vehicle (safe to re-run)
python -m uvicorn app.main:app --reload   # http://localhost:8000, docs at /docs
```
Optional: `python scripts/import_scraper_data.py` (repo root) to load real scraped vehicles instead
of just the one seed vehicle. `ANTHROPIC_API_KEY` env var is required for the chat endpoints
(catalog endpoints work without it). Note: on some setups the bare `uvicorn` command isn't on
`PATH` — use `python -m uvicorn` as above.

**Frontend** (from `frontend/`):
```bash
npm install
npm run dev        # http://localhost:5173, expects the backend at http://localhost:8000/api
npm run test       # Vitest
npm run build      # type-check + production build
```
Override the backend URL with `VITE_API_BASE_URL` if needed.

**Scraper** (from repo root, same venv as backend):
```bash
python -m scraper.main
pytest scraper/tests/ -v
```

## Known gaps

- Conversation history/state isn't persisted (in-memory, single-process only).
- `min_seats` is accepted by the API but not actually filterable yet.
- Over-budget vehicles are hard-excluded; the "include with a warning flag" behavior isn't built.
- The AI layer hasn't been exercised against a live Claude API key — prompt behavior (JSON-only
  output, Czech free text) is unverified against the real model.
- Scraper-imported vehicles have no equipment (option) data.
