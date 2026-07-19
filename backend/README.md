# DriveWise AI – backend

FastAPI + SQLAlchemy + PostgreSQL. See `doc/prompt/CLAUDE.md` for repo-wide conventions and
`doc/api-contract.md` for the endpoint/schema contract.

Currently scaffolded: the data layer only (`app/db`, `app/models`, Alembic migrations). The API
layer (`app/api`, `app/schemas`, `app/services`, `app/ai`) doesn't exist yet — `fastapi`/`pydantic`
aren't in `requirements.txt` for that reason; they'll be added when that layer is built.

## Setup

```bash
python -m venv .venv
.venv/Scripts/activate        # Windows; `source .venv/bin/activate` elsewhere
pip install -r requirements.txt
```

Set `DATABASE_URL` (or create a `.env` file) to point at a real PostgreSQL instance, e.g.:

```
DATABASE_URL=postgresql+psycopg://drivewise:drivewise@localhost:5432/drivewise
```

Defaults to that same local value if unset.

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
