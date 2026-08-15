# DriveWise AI (Car Selector)

AI-assisted car selection tool: chat about what you need, get vehicle recommendations filtered and
ranked against a catalog, with an AI-generated explanation for each pick. See
[`doc/main.md`](doc/main.md) for the original brief and [`doc/po/MVP.md`](doc/po/MVP.md) for what's
actually in scope right now.

## Status

Frontend chat UI, backend catalog/recommendation API, and the scraper each work, but are **not
yet wired together end to end**:

- The frontend chat flow currently runs against a scripted mock, not the real backend.
- The backend's catalog is hand-seeded from a couple of real price lists in `storage/cars/`, not
  populated by the scraper.
- The scraper writes into its own separate database — there's no import step into the backend's
  catalog yet.

See each subproject's README for specifics, and `doc/api-contract.md` "open items" for known gaps.

## Repository structure

```
backend/    FastAPI + SQLAlchemy + SQLite (dev default) / PostgreSQL (target) — REST API,
            recommendation engine, Claude integration
frontend/   React + TypeScript + Vite + Tailwind — chat UI, results/comparison views
scraper/    Standalone Python service — downloads & parses manufacturer PDF price lists
doc/        Architecture, API contract, DB schema, scope decisions — see doc/README.md for the index
scripts/    Convenience launchers (e.g. run-ui.sh/.bat/.ps1 — frontend only, mock-backed)
storage/    Sample source price-list PDFs used to hand-seed backend test/demo data
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

## Documentation

Start at [`doc/README.md`](doc/README.md) for an index of what's a current source of truth versus
historical/brainstorm material.
