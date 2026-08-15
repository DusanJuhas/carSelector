# DriveWise AI (Car Selector)

AI-assisted car selection tool: chat about what you need, get vehicle recommendations filtered and
ranked against a catalog, with an AI-generated explanation for each pick. See
[`doc/main.md`](doc/main.md) for the original brief and [`doc/po/MVP.md`](doc/po/MVP.md) for what's
actually in scope right now.

## Status

Frontend chat UI, backend catalog/recommendation API, and the scraper each work, but are **not
fully wired together end to end**:

- The frontend chat flow currently runs against a scripted mock, not the real backend.
- The backend's catalog can be populated two ways: hand-seeded demo data (`python -m app.db.seed`,
  a couple of real price lists in `storage/cars/`) or a real import of everything the scraper has
  found (`python scripts/import_scraper_data.py`) — see that script's docstring for exactly what it
  does and doesn't carry over (e.g. equipment/options aren't imported yet, no surcharge data to
  import). This import is a manual/periodic step, not a live pipeline — re-run it after every scrape.

See each subproject's README for specifics, and `doc/api-contract.md` "open items" for known gaps.

## Repository structure

```
backend/    FastAPI + SQLAlchemy + SQLite (dev default) / PostgreSQL (target) — REST API,
            recommendation engine, Claude integration
frontend/   React + TypeScript + Vite + Tailwind — chat UI, results/comparison views
scraper/    Standalone Python service — downloads & parses manufacturer PDF price lists
doc/        Architecture, API contract, DB schema, scope decisions — see doc/README.md for the index
scripts/    Cross-cutting glue — frontend launchers (run-ui.sh/.bat/.ps1) and
            import_scraper_data.py (scraper.db → drivewise.db)
storage/    All local DB files + PDF copies for backend/ and scraper/ — see storage/README.md
.claude/    Claude Code project config: skills (doc/prompt/CLAUDE.md is the main conventions file)
requirements.txt, requirements-dev.txt   Python deps for backend/ + scraper/ (one shared venv;
            frontend/ is Node, see frontend/package.json)
```

## Quickstart

**See the chat UI (no backend needed — runs on a mock):**

```bash
./scripts/run-ui.sh     # or scripts\run-ui.bat / scripts\run-ui.ps1 on Windows
```

**Run the full stack:**

1. Python setup (once, for backend/ and scraper/):
   ```bash
   python -m venv .venv
   .venv/Scripts/activate    # Windows; `source .venv/bin/activate` elsewhere
   pip install -r requirements-dev.txt
   ```
2. Backend — see [`backend/README.md`](backend/README.md) (SQLite by default, no server to
   install; needs `ANTHROPIC_API_KEY` for the AI layer)
3. Frontend — see [`frontend/README.md`](frontend/README.md)
4. Scraper (optional, populates its own DB independently) — see [`scraper/README.md`](scraper/README.md)
5. To load real scraped data into the backend's catalog instead of (or alongside) the demo seed:
   `python scripts/import_scraper_data.py` (safe to re-run after each scrape)

## Documentation

Start at [`doc/README.md`](doc/README.md) for an index of what's a current source of truth versus
historical/brainstorm material.
