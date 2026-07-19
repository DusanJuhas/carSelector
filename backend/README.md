# DriveWise AI – backend

FastAPI + SQLAlchemy + PostgreSQL. See `doc/prompt/CLAUDE.md` for repo-wide conventions and
`doc/api-contract.md` for the endpoint/schema contract (source of truth for request/response
shapes — keep it in sync with `app/schemas` when either changes).

## Layout

```
app/
  db/        engine/session, declarative Base
  models/    SQLAlchemy models (the catalog: brands/models/trims/powertrains/configurations/...)
  schemas/   Pydantic request/response shapes, matching doc/api-contract.md
  services/  business logic - catalog queries, the deterministic recommendation engine,
             conversation orchestration
  ai/        the only place Claude API calls are allowed to happen (CLAUDE.md convention)
  api/       FastAPI routers
  main.py    app instance, router wiring, error-shape exception handler
```

## Setup

```bash
python -m venv .venv
.venv/Scripts/activate        # Windows; `source .venv/bin/activate` elsewhere
pip install -r requirements-dev.txt   # requirements.txt + pytest/httpx for running tests
```

Set `DATABASE_URL` (or create a `.env` file) to point at a real PostgreSQL instance:

```
DATABASE_URL=postgresql+psycopg://drivewise:drivewise@localhost:5432/drivewise
```

Defaults to that same local value if unset. The AI layer additionally needs:

```
ANTHROPIC_API_KEY=sk-ant-...
CLAUDE_MODEL=claude-sonnet-5   # optional, this is the default
```

There is no default for `ANTHROPIC_API_KEY` — `app/ai/client.py` raises loudly if it's missing
rather than running the AI layer silently disabled. The conversation endpoints degrade to a
`503 ai_not_configured` response without it; the catalog endpoints (brands/models/vehicles) don't
need it at all.

**The AI layer (`app/ai/requirement_interpreter.py`, `app/ai/explanation_generator.py`) was
written without access to a live API key and has not been exercised against the real Claude API.**
Verify prompt behavior (does it reliably return JSON-only, is the follow-up-question quality
reasonable) before relying on it.

## Run the API

```bash
uvicorn app.main:app --reload
```

Interactive docs at `http://localhost:8000/docs`.

## Tests

```bash
pytest
```

`tests/conftest.py` spins up a throwaway in-memory SQLite DB per test (via `Base.metadata.create_all`,
not Alembic), seeds it with real sample data drawn from the Mazda CX-5 price list in
`storage/cars/`, and drives the FastAPI app through `TestClient` - so the catalog endpoints
(brands/models/vehicles/compare) are exercised end to end, not just imported. The conversation
endpoints are tested only up to the point that requires a live Claude API call (they correctly
503 without a key); the AI layer itself isn't covered by this suite.

One SQLite-only quirk worth knowing if you extend the fixtures: SQLAlchemy's `BigInteger` primary
key doesn't get SQLite's autoincrement rowid-aliasing (only a literal `Integer` PK does) - the
fixtures assign every id explicitly rather than relying on autoincrement. This doesn't affect
Postgres, where the migration renders `BIGSERIAL` (see below).

## Migrations

```bash
alembic upgrade head          # apply all migrations
alembic upgrade head --sql    # preview the DDL without needing a live DB (offline mode)
alembic revision --autogenerate -m "message"   # generate a new migration from model changes
```

The first migration (`create catalog schema`) was authored by autogenerating against a throwaway
scratch SQLite DB (no local Postgres was available at authoring time) and then hand-verified by
rendering it as real Postgres DDL via `alembic upgrade head --sql` — the emitted `op.create_table`
calls use the actual model Column/type objects, so they compile correctly for whichever dialect
`DATABASE_URL` points at; nothing SQLite-specific leaked into the migration itself. One thing
autogenerate did *not* catch and had to be added by hand: Postgres native enum types it creates
implicitly aren't dropped again by the generated `downgrade()`, which would break a
downgrade-then-upgrade round trip — see the `DROP TYPE` loop at the bottom of
`alembic/versions/6579b05df670_create_catalog_schema.py`.

## Known gaps (see doc/api-contract.md "open items" for the full list)

- Conversation state is in-memory only (`app/services/conversation.py`) - no persistence, no
  multi-process support. There are no `conversations`/`messages` tables in the DB schema yet.
- `min_seats` is accepted by `StructuredRequirements` and the `/api/vehicles` query params but
  isn't actually filterable - no source document states seat count.
- The recommendation engine's budget handling is a hard filter; the design concept's "include a
  slightly-over-budget car with a warning flag" behavior isn't implemented (`flag` is always null).
