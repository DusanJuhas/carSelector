# DriveWise AI – backend

FastAPI + SQLAlchemy + PostgreSQL (target) / SQLite (current default, see Database below). See
`doc/prompt/CLAUDE.md` for repo-wide conventions and `doc/api-contract.md` for the endpoint/schema
contract (source of truth for request/response shapes — keep it in sync with `app/schemas` when
either changes).

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

Python dependencies are consolidated in one `requirements.txt`/`requirements-dev.txt` pair at the
**repo root** (shared with `scraper/` — see there for why), so the venv lives at the repo root too,
not here:

```bash
cd ..                          # repo root, if you're in backend/
python -m venv .venv
.venv/Scripts/activate         # Windows; `source .venv/bin/activate` elsewhere
pip install -r requirements-dev.txt   # requirements.txt + pytest/httpx for running tests
cd backend
```

Commands below (`uvicorn`, `alembic`, `pytest`) still need to run with `backend/` as the working
directory (that's where `app/`, `alembic.ini`, etc. live) — only dependency installation moved.

`DATABASE_URL` defaults to a SQLite file at `storage/drivewise.db` (repo root, see
`storage/README.md`) — no database server to install, see Database below. To use PostgreSQL
instead, set `DATABASE_URL` (or create a `.env` file):

```
DATABASE_URL=postgresql+psycopg://drivewise:drivewise@localhost:5432/drivewise
```

The AI layer additionally needs:

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

## Database

SQLite (a local file, `storage/drivewise.db`, gitignored) is the default for now, so the app runs
without installing anything database-related. The schema (`app/models/`, the Alembic migration) is
written to stay dual-dialect rather than SQLite-only — see `app/db/base.py`'s `BigIntPK` (SQLite
only auto-increments a PK when the column is literally `INTEGER`, unlike Postgres's `BIGSERIAL`)
and the `prices` table's partial unique index (`postgresql_where`/`sqlite_where` pair) — so
switching `DATABASE_URL` to Postgres later needs no model/migration changes.

```bash
alembic upgrade head      # creates storage/drivewise.db and the schema in it
python -m app.db.seed     # seeds one real, hand-verified vehicle (Mazda CX-5) - safe to re-run,
                           # skips if the DB already has data
```

`python -m app.db.seed` also calls `Base.metadata.create_all()` first, so on a totally fresh
checkout you can skip straight to it without running `alembic upgrade head` separately — Alembic
remains the source of truth for schema history either way (`alembic_version` gets stamped once you
do run it).

For real (not hand-seeded) catalog data, `python scripts/import_scraper_data.py` (repo root) loads
whatever `scraper/` has found in `storage/scraper.db` — see that script's docstring and
`storage/README.md` for what it does and doesn't carry over. Both can populate the same DB; run
either or both.

## Run the API

```bash
uvicorn app.main:app --reload
```

Interactive docs at `http://localhost:8000/docs`. Try `GET /api/brands` or `GET /api/vehicles`
after seeding to see real data.

## Tests

```bash
pytest
```

`tests/conftest.py` spins up a throwaway in-memory SQLite DB per test (via `Base.metadata.create_all`,
not Alembic), seeds it via `app.db.seed.seed_demo_data()` — the same real sample data drawn from
the Mazda CX-5 price list in `storage/cars/` that `python -m app.db.seed` writes to the persistent
dev DB, one source of truth for both — and drives the FastAPI app through `TestClient` - so the
catalog endpoints (brands/models/vehicles/compare) are exercised end to end, not just imported. The
conversation endpoints are tested only up to the point that requires a live Claude API call (they
correctly 503 without a key); the AI layer itself isn't covered by this suite.

`seed_demo_data()` assigns every id explicitly rather than relying on autoincrement - not required
for correctness (see `BigIntPK` below, which makes autoincrement work on SQLite too), but it keeps
the seed deterministic and makes cross-referencing ids (e.g. `config_prime_2wd_id`) trivial in
tests.

## Migrations

```bash
alembic upgrade head          # apply all migrations
alembic upgrade head --sql    # preview the DDL without needing a live DB (offline mode)
alembic revision --autogenerate -m "message"   # generate a new migration from model changes
```

The first migration (`create catalog schema`) was authored by autogenerating against a throwaway
scratch SQLite DB and then hand-verified by rendering it as real Postgres DDL via
`alembic upgrade head --sql` — the emitted `op.create_table` calls use the actual model
Column/type objects, so they compile correctly for whichever dialect `DATABASE_URL` points at.
Since SQLite became the actual default (not just an authoring scratch DB), three spots needed
dialect-aware handling rather than being left Postgres-only, all verified with a real
`alembic upgrade head` → `downgrade base` → `upgrade head` round trip against SQLite directly (not
just `--sql` rendering):
- Every model's primary key uses `app/db/base.py`'s `BigIntPK` instead of bare `BigInteger` -
  SQLite only auto-increments a PK when the column type is exactly `INTEGER`, so a bare
  `BigInteger` PK (which is fine on Postgres/`BIGSERIAL`) silently never autoincrements on SQLite.
- The `prices` table's partial unique index needs both `postgresql_where` and `sqlite_where` - the
  Postgres dialect happens to accept a plain string for the former, but SQLite's DDL compiler
  requires an actual `text(...)` expression for the latter.
- Postgres native enum types (created implicitly, one per `Enum` column) aren't dropped by the
  generated `downgrade()`, which breaks a downgrade-then-upgrade round trip - fixed with a
  `DROP TYPE` loop, guarded to run only on `dialect.name == "postgresql"` since SQLite has no
  native enum type at all (`Enum` renders as plain `VARCHAR`, with no DB-level CHECK either -
  SQLAlchemy's `Enum` defaults to `create_constraint=False` - so validity is enforced by
  Pydantic/the ORM layer, not the DB, on SQLite) - see the bottom of
  `alembic/versions/6579b05df670_create_catalog_schema.py`. `alembic/versions/e49d32df7bd1_*.py`
  (adding the `hybrid` fuel type) is a second example of the same postgres/sqlite split, this time
  via `batch_alter_table` on the SQLite side (SQLite can't redefine a column's type in place).

## Known gaps (see doc/api-contract.md "open items" for the full list)

- Conversation state is in-memory only (`app/services/conversation.py`) - no persistence, no
  multi-process support. There are no `conversations`/`messages` tables in the DB schema yet.
- `min_seats` is accepted by `StructuredRequirements` and the `/api/vehicles` query params but
  isn't actually filterable - no source document states seat count.
- The recommendation engine's budget handling is a hard filter; the design concept's "include a
  slightly-over-budget car with a warning flag" behavior isn't implemented (`flag` is always null).
- `scripts/import_scraper_data.py` never populates `option_items`/`option_availability` (equipment)
  - the scraper's source data has no surcharge amount, which the schema requires for `optional`
    rows - so `standard_equipment`/`optional_equipment` are empty for every scraper-imported vehicle.
