---
name: drivewise-data-model
description: The PostgreSQL catalog schema and ORM/validation conventions for DriveWise AI — brands, models, trims, powertrains, configurations, colors, option_items, option_availability, prices, and source_documents — plus their SQLAlchemy models and Pydantic schemas. Use this whenever writing or changing anything that touches the vehicle database — models, migrations, queries, seed data, or the shape of vehicle objects returned by the API. Reach for it before defining a new table or column, writing a SQLAlchemy query, or building a Pydantic model for vehicle data, even if the task only mentions "the database" or "car data" generally.
---

# DriveWise AI — Data Model

The catalog is normalized across ten tables (`backend/app/models/`), built around one core idea:
a **`configuration`** (trim × powertrain) is the actual sellable unit everything else hangs off of
— prices, option availability, and color availability are all scoped to a `configuration_id`, not
to a bare model or trim. Populated from whatever a source document actually lists as orderable,
never a computed trim × powertrain cross product (not every trim offers every engine).

Source of truth for the schema: `backend/app/models/*.py` and `doc/db/db-structure.md`. This skill
is a map of it, not a copy — re-check the models if this drifts.

## Schema

```
brands            id, slug, name

models            id, brand_id → brands, slug, name, category (body type), model_year, description

trims             id, model_id → models, name, display_order, description

powertrains       id, model_id → models, manufacturer_code, fuel_type (enum), transmission,
                   drivetrain (enum: fwd/rwd/awd), displacement_cc, power_kw/hp, torque_nm,
                   consumption_min/max + unit, co2_min/max_g_km, emission_standard, fuel_tank_l

configurations     id, trim_id → trims, powertrain_id → powertrains, manufacturer_code
                   (UNIQUE(trim_id, powertrain_id) — the sellable unit)

colors             id, model_id → models, name, manufacturer_code, finish_type (enum)

configuration_colors  id, configuration_id → configurations, color_id → colors, surcharge_amount, currency

option_items       id, model_id → models, category (enum: equipment/package/warranty/service),
                   code, name, description  (the open-ended long tail: features, packages, warranties)

option_availability  id, option_item_id → option_items, configuration_id → configurations,
                   availability (enum: standard/optional/unavailable), surcharge_amount, currency

prices             id, configuration_id → configurations, source_document_id → source_documents,
                   market, currency, list_price, discount_amount, price_incl_vat, price_excl_vat,
                   vat_rate, lowest_price_30d, valid_from, valid_to, scraped_at
                   — APPEND-ONLY history; "current price" = the row with valid_to IS NULL
                   (enforced by a partial unique index per configuration+market)

source_documents   id, model_id → models, file_path, document_type (enum), market, locale,
                   effective_date, campaign_valid_from/to, retrieved_at
                   — provenance for every price row
```

Fields from the original domain spec map onto this schema as: brand → `brands`, model → `models`,
body type → `models.category`, fuel type/AWD/power → `powertrains`, price → `prices`, optional
equipment → `option_items`/`option_availability`. Seats and trunk capacity have **no dedicated
column yet** — no source price list states them; see `doc/api-contract.md`'s "open items" before
adding one.

## Conventions

- **SQLAlchemy** models, one class per table (`backend/app/models/`), relationships via `relationship()`. `CarModel` (not `Model` — avoids colliding with ORM-framework naming) is the class for the `models` table.
- **Pydantic** schemas for all API I/O (`backend/app/schemas/`) — never return raw ORM objects.
- Pydantic schema shapes must match `doc/api-contract.md`. If you change a catalog field, update the contract in the same change.
- Money: `list_price`/`price_incl_vat`/`price_excl_vat` + `currency` always travel together — never assume CZK, never derive excl-VAT from an assumed rate when the source doesn't state one.
- `prices` is append-only — a price change is a new row (`valid_from` = today) after closing the previous row (`valid_to` = today), never an in-place update.

## Query guidance

- The recommendation engine reads candidate vehicles through query helpers that filter by the AI layer's structured parameters (budget, body_type, fuel_type, drivetrain, etc.) — see `drivewise-ai-recommendations`.
- Join eagerly (trim, powertrain, current price) when returning a full vehicle detail; keep list/search queries lean.

## Database: SQLite by default, Postgres is the target

`DATABASE_URL` defaults to a local SQLite file (`backend/drivewise.db`) so the backend runs without
installing Postgres — see `backend/README.md`'s Database section. The schema/migration is kept
dual-dialect on purpose (`app/db/base.py`'s `BigIntPK`, the `prices` partial index's
`postgresql_where`/`sqlite_where` pair, the Postgres-only `DROP TYPE` downgrade guard) — don't add
Postgres-only DDL to a model or migration without a SQLite equivalent, and don't assume Postgres
when writing raw SQL (stick to the SQLAlchemy query layer, which is already dialect-agnostic).

## How the catalog actually gets populated today

There is **no live pipeline yet** from the `scraper/` service into this schema — they're two
separate databases with two separate schemas. `backend/app/db/seed.py`'s `seed_demo_data()` is the
one source of truth for the demo dataset (real Mazda CX-5 price-list data from `storage/cars/`),
shared by `backend/tests/conftest.py` (in-memory SQLite, per test) and `python -m app.db.seed`
(the persistent dev SQLite file); the `scraper/` service writes into its own SQLite DB
(`scraper/storage/scraper.db`) using a different, document-centric schema
(`document`/`variant`/`price_history`/`equipment`) — see `drivewise-scraper`. Building the
ETL/import step between the two is not done; don't assume it exists.
