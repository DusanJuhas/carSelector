# Database Brainstorm 1 — Data Needed & Storage Options

Brainstorm from a database-engineering perspective, covering what data the Car Selector needs and how/where to store it.

---

## 1. What data actually needs to live in the system

Three tiers of data, drawn from the functional requirements in [main.md](../main.md):

- **Vehicle catalog** — brand, model, year/generation, trim, body type, seats, fuel type, engine power, consumption, trunk size, AWD, price. This is the data in the spec's example JSON.
- **Derived/enriched attributes** — attributes the AI needs but a raw pricelist won't state explicitly (e.g. "suitable for gravel roads," "family-friendly," "long-trip comfort"). Either computed via rules or tagged (manually or LLM-assisted).
- **Conversation & recommendation data** — user sessions, extracted structured requirements per query, which vehicles were shown/ranked and why (for explanations and later analytics).

The pricelist ingestion problem sits entirely in tier 1 and is the part most likely to consume disproportionate effort.

---

## 2. The pricelist ingestion problem

Manufacturer pricelists arrive as PDFs, Excel exports, or scraped HTML — each with different trim/option naming, different units (kW vs hp, l vs gal), and they change over time (new model year, price updates, discontinued trims).

**a) Keep a raw staging layer separate from canonical data**
- Store an immutable raw staging table (source file, brand, ingestion date, raw extracted rows as JSONB/text) separately from the canonical `vehicles` table.
- Why: extraction logic will be wrong at times (especially from PDFs); re-running parsing against the original data shouldn't require re-scraping/re-uploading. Also gives an audit trail for "why does this price look wrong."
- Trade-off: more tables/pipeline complexity than parsing straight into the final schema — acceptable given the payoff, but a real cost for a prototype-first timeline (see [MVP.md](../po/MVP.md), which defers building this pipeline).

**b) Price as a fact table, not a column**
- Prices vary by trim/engine/market and change over time. A single `price` column on `vehicles` breaks the moment history or trim-level variance is needed.
- Better: `vehicle_prices (vehicle_id, trim, price, currency, valid_from, valid_to, source)`. Answers "current price," "price 6 months ago," and "compare trims" without schema changes.
- Trade-off: more joins for the common "just show current price" case — mitigate with a materialized view or a denormalized `current_price` cache on the vehicle row.

---

## 3. Schema shape for the vehicle catalog — three options considered

### Option A: Fully normalized relational (Postgres)
Tables: `brands`, `models`, `model_years`, `trims`, `vehicles`, `vehicle_prices`.
- ✅ Strong integrity, easy SQL filter/sort/rank, mature tooling.
- ❌ Rigid — every new spec attribute needs a migration. Manufacturers don't agree on what attributes exist per body type (a van's storage config isn't a sedan's trunk).

### Option B: Relational core + JSONB "specs" column — **recommended**
Fixed columns for attributes every recommendation query filters on (seats, body_type, fuel_type, price, AWD), plus a `specs JSONB` column for the long tail (infotainment, ground clearance, towing, etc. — whatever a given pricelist happens to include).
- ✅ Best of both: SQL indexing/filtering on hot attributes, flexibility for messy/inconsistent source data without constant migrations. Postgres JSONB + GIN index keeps even the flexible fields reasonably queryable.
- ❌ Data quality discipline gets harder — nothing stops `trunk_capacity` from being a string in one row and an int in another unless enforced at ingestion time.
- This directly absorbs the "messy pricelist" problem without over-engineering, and is the option carried into [MVP.md](../po/MVP.md).

### Option C: Document store (MongoDB) for the whole catalog
- ✅ Naturally matches inconsistent per-brand/per-body-type attributes; no migrations.
- ❌ Loses relational integrity for price-history/comparison logic, and "filter + rank across many attributes" is exactly the workload relational engines handle better. Also fragments the stack (spec already lists Postgres/SQLite, not Mongo). Avoided.

---

## 4. Postgres vs SQLite

- **SQLite**: fine for prototype/demo, zero ops overhead, but weak JSONB support and no concurrent-write story — breaks as soon as an ingestion pipeline runs alongside the app.
- **Postgres**: JSONB + GIN indexes solve the flexible-spec problem natively, handles concurrent ingestion + app reads cleanly, and later supports `pgvector` for embedding-based semantic search over vehicle descriptions (synergy with the RAG bonus feature).
- **Decision: Postgres from day one**, rather than migrating later — the JSONB piece is load-bearing for the messy-pricelist problem, not just a nice-to-have.

---

## 5. Search vs. filter

The AI Requirement Interpreter outputs structured filters (`min_seats`, `body_type`, etc.) *and* soft/fuzzy criteria ("suitable for long trips").
- Structured filters map cleanly to indexed SQL columns.
- Soft criteria either need a rules layer (tag vehicles with derived boolean flags at ingestion time) or vector similarity search (embed vehicle descriptions, embed the query, cosine-similarity rank). `pgvector` keeps this in the same database rather than bolting on a separate vector store.
- **MVP decision**: rule-based/SQL ranking only — simpler and more explainable than vector search, and explainability is a hard requirement. RAG/vector search deferred to [Version2.md](../po/Version2.md).

---

## 6. Storing original source documents (pricelists, car-parts PDFs, several MB each)

### Postgres BYTEA / Large Objects
- Functionally fine — Postgres TOAST auto-compresses/chunks large values, a few-MB PDF isn't a technical problem.
- Large Objects (`lo`) offer streaming APIs for very large files but are clunkier (permissions aren't per-row, orphan cleanup needs `vacuumlo`, `pg_dump` needs `-b`) — not worth it at these file sizes.
- **Real problem is operational, not functional**: every stored PDF bloats `pg_dump`/`pg_basebackup` size and time, pollutes the shared buffer cache (crowding out actual query data), and inflates WAL on every insert/update. At hundreds of pricelists × multiple revisions, backup/replication get noticeably heavier for no query benefit (file bytes are never `WHERE`-filtered).
- ✅ One upside: transactional consistency is automatic — file and metadata commit/rollback together, no orphan-file bookkeeping needed.

### Filesystem (path stored in Postgres)
- ✅ Simple, cheap, fast, trivial to serve statically, easy to `rsync` for backup.
- ❌ Breaks transactional consistency — a DB row can point to a file that failed to write, or vice versa; requires hand-rolled two-phase write/commit handling.
- ❌ Doesn't scale across multiple app instances/containers without shared storage — awkward given the Docker-based setup already planned.

### Object storage (S3-compatible / MinIO / Azure Blob) — **recommended**
- ✅ Purpose-built for this. Decoupled from the DB — no backup bloat, no buffer cache pollution. Built-in versioning (handles "pricelist got updated" naturally), presigned URLs so the frontend can fetch a PDF directly without proxying through the backend, lifecycle policies for cleanup.
- ✅ MinIO gives an S3-compatible API runnable in the same Docker Compose as the rest of the stack — no cloud dependency for local dev, drop-in swap for real S3/Azure Blob later.
- ❌ Same two-phase "commit row + confirm blob" concern as filesystem, but it's a well-known pattern: upload → get checksum/ETag back → write the DB row referencing it → treat unreferenced blobs as garbage-collectable.

### MongoDB GridFS
- Purpose-built for files >16MB, but adopting it means standing up a second database purely for blob storage while Postgres remains the system of record for everything else — added operational surface (two things to back up, monitor, secure) without beating object storage on any relevant axis. Only makes sense if Mongo were already the primary store. **Avoided.**

### Decision
MinIO (or S3-compatible storage) for original PDFs, Postgres holding only the reference — `(source_file_key, brand, bucket/path, checksum, uploaded_at, parse_status)` in the raw staging table. Not BYTEA, not filesystem, not Mongo. This is a [Version2.md](../po/Version2.md) concern — no PDFs are ingested at MVP, so no object storage setup is required yet, but the schema is designed so it can absorb this without rework.

---

## Summary of decisions carried into planning docs

| Decision | Chosen | Rationale doc |
|---|---|---|
| Primary DB engine | PostgreSQL | Section 4 |
| Catalog schema shape | Relational core + JSONB specs column | Section 3 |
| Price modeling | Fact table with validity range (Version 2), single column (MVP) | Section 2b |
| Soft-criteria matching | Rule-based scoring (MVP), pgvector/RAG (Version 2) | Section 5 |
| Original document storage | Object storage (MinIO/S3), reference-only in Postgres | Section 6 |
| Ingestion pipeline | Deferred to Version 2; MVP uses hand-curated seed data | Section 2, [MVP.md](../po/MVP.md) |

See [MVP.md](../po/MVP.md) and [Version2.md](../po/Version2.md) for how these decisions map onto feature sequencing.
