# Database Structure

Concrete table structure following the decisions in [brainstorm1.md](./brainstorm1.md): PostgreSQL, relational core + JSONB specs column, object storage (MinIO/S3-compatible) for original source documents with only a reference stored in Postgres.

**Current implementation status:** the schema below is implemented in `backend/app/models/` and
`backend/alembic/`, running on **SQLite by default** (`storage/drivewise.db` — see
`storage/README.md`) so the app doesn't need a local Postgres install yet — see
`backend/README.md`'s Database section. The schema is kept dual-dialect (Postgres remains the
target), not SQLite-only.

Two parts:
1. **MVP schema** — the only tables needed to ship the MVP described in [MVP.md](../po/MVP.md). Hand-seeded catalog, no ingestion pipeline, no source documents yet.
2. **Object storage / ingestion schema** — the [Version2.md](../po/Version2.md) tables that reference MinIO/S3. Documented now so the MVP schema doesn't need reshaping when this lands.

---

## 1. MVP Schema

### `vehicles`

Single denormalized table — brand/model as plain columns rather than separate lookup tables. At MVP catalog size (~50–150 hand-seeded rows) a `brands`/`models` normalization buys referential integrity you don't need yet at the cost of joins on every recommendation query; revisit only if an admin/dedup use case demands it.

```sql
CREATE TABLE vehicles (
    id                BIGSERIAL PRIMARY KEY,
    brand             TEXT NOT NULL,
    model             TEXT NOT NULL,
    trim              TEXT,
    model_year        SMALLINT NOT NULL,
    body_type         TEXT NOT NULL,
        CHECK (body_type IN ('suv', 'sedan', 'hatchback', 'wagon', 'van', 'pickup', 'coupe')),
    seats             SMALLINT NOT NULL CHECK (seats BETWEEN 1 AND 9),
    fuel_type         TEXT NOT NULL,
        CHECK (fuel_type IN ('petrol', 'diesel', 'hybrid', 'phev', 'electric')),
    engine_power_kw   SMALLINT,
    consumption       NUMERIC(5,2),        -- l/100km (combustion/hybrid) or kWh/100km (electric)
    trunk_capacity_l  SMALLINT,
    awd               BOOLEAN NOT NULL DEFAULT FALSE,
    price             NUMERIC(12,2) NOT NULL CHECK (price > 0),
    currency          CHAR(3) NOT NULL DEFAULT 'EUR',
    specs             JSONB NOT NULL DEFAULT '{}',  -- long-tail attributes: infotainment, ground clearance, towing, etc.
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

`body_type` and `fuel_type` use `TEXT` + `CHECK` rather than Postgres `ENUM` — easier to extend during MVP iteration (`ALTER TABLE ... DROP CONSTRAINT / ADD CONSTRAINT`) than an enum type, at the minor cost of no compile-time type safety.

**Indexes** — cover the columns the recommendation engine actually filters/sorts on:

```sql
CREATE INDEX idx_vehicles_body_type   ON vehicles (body_type);
CREATE INDEX idx_vehicles_fuel_type   ON vehicles (fuel_type);
CREATE INDEX idx_vehicles_seats       ON vehicles (seats);
CREATE INDEX idx_vehicles_price       ON vehicles (price);
CREATE INDEX idx_vehicles_awd         ON vehicles (awd) WHERE awd = TRUE;
CREATE INDEX idx_vehicles_specs_gin   ON vehicles USING GIN (specs);

-- Common combined filter: body type + seats within a budget
CREATE INDEX idx_vehicles_filter_combo ON vehicles (body_type, seats, price);
```

That's the entire MVP schema — one table. No `brands`/`models` lookup tables, no price history, no session/conversation persistence (chat state can live in the application layer for MVP; nothing in the spec's MVP scenario requires it durable in the DB).

---

## 2. Object Storage / Ingestion Schema (Version 2 — not needed until PDF ingestion starts)

These tables implement the "raw staging layer" and "reference-only" object storage decisions from [brainstorm1.md](./brainstorm1.md#6-storing-original-source-documents-pricelists-car-parts-pdfs-several-mb-each). Not created for MVP — included here so the eventual migration is additive, not a redesign.

### `source_documents`

One row per original file uploaded to MinIO/S3. Postgres stores only the reference; the PDF bytes live in the bucket.

```sql
CREATE TABLE source_documents (
    id                 BIGSERIAL PRIMARY KEY,
    brand              TEXT NOT NULL,
    document_type      TEXT NOT NULL CHECK (document_type IN ('pricelist', 'car_parts_catalog')),
    storage_bucket     TEXT NOT NULL,
    storage_key        TEXT NOT NULL,          -- object path/key within the bucket
    original_filename  TEXT NOT NULL,
    content_type       TEXT NOT NULL DEFAULT 'application/pdf',
    size_bytes         BIGINT NOT NULL,
    checksum_sha256    TEXT NOT NULL,
    uploaded_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    parse_status       TEXT NOT NULL DEFAULT 'pending'
        CHECK (parse_status IN ('pending', 'parsed', 'failed')),
    parsed_at          TIMESTAMPTZ,
    UNIQUE (storage_bucket, storage_key)
);
```

Write order matters for consistency: upload to the bucket first, get back a checksum/ETag, **then** insert this row referencing it. Treat any bucket object with no matching row as garbage-collectable.

### `raw_vehicle_extracts`

Immutable staging rows capturing what was extracted from a source document, before normalization into `vehicles`. Lets extraction logic be re-run against the original data without re-uploading, and gives an audit trail from a live catalog row back to the document it came from.

```sql
CREATE TABLE raw_vehicle_extracts (
    id                     BIGSERIAL PRIMARY KEY,
    source_document_id     BIGINT NOT NULL REFERENCES source_documents(id),
    raw_row                JSONB NOT NULL,       -- extracted fields as-parsed, pre-normalization
    extracted_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    normalized_vehicle_id  BIGINT REFERENCES vehicles(id)  -- set once the row has been normalized into vehicles
);

CREATE INDEX idx_raw_extracts_source_document ON raw_vehicle_extracts (source_document_id);
```

### `vehicle_prices` (price history — also Version 2)

Replaces the single `vehicles.price` column once real pricelists introduce history and trim-level variance. Referenced in [brainstorm1.md §2b](./brainstorm1.md#2-the-pricelist-ingestion-problem).

```sql
CREATE TABLE vehicle_prices (
    id           BIGSERIAL PRIMARY KEY,
    vehicle_id   BIGINT NOT NULL REFERENCES vehicles(id),
    trim         TEXT,
    price        NUMERIC(12,2) NOT NULL CHECK (price > 0),
    currency     CHAR(3) NOT NULL DEFAULT 'EUR',
    valid_from   DATE NOT NULL,
    valid_to     DATE,                      -- NULL = currently in effect
    source_document_id BIGINT REFERENCES source_documents(id),
    UNIQUE (vehicle_id, trim, valid_from)
);

CREATE INDEX idx_vehicle_prices_vehicle ON vehicle_prices (vehicle_id) WHERE valid_to IS NULL;
```

At migration time, `vehicles.price`/`currency` become a denormalized "current price" cache (or a materialized view over `vehicle_prices WHERE valid_to IS NULL`) to keep the common "show current price" query a single-table read.

---

## Summary

| Table | Phase | Purpose |
|---|---|---|
| `vehicles` | MVP | Catalog + specs, single current price |
| `source_documents` | Version 2 | Reference to original PDFs in MinIO/S3 (bytes never touch Postgres) |
| `raw_vehicle_extracts` | Version 2 | Immutable staging between raw extraction and normalized `vehicles` rows |
| `vehicle_prices` | Version 2 | Price history / trim-level variance, replaces `vehicles.price` as source of truth |
