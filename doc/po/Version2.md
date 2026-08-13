# Car Selector — Version 2 / Post-MVP Scope

## Goal

Features that are genuine parts of the product vision but were deferred from [MVP.md](./MVP.md) because they either depend on the core loop already working, or represent open-ended effort disproportionate to their value before the core loop is proven.

## Deferred Features

| Feature | Why it can wait |
|---|---|
| Pricelist / car-parts PDF ingestion pipeline | Open-ended parsing problem — every manufacturer formats pricelists differently (PDF, spreadsheet, scraped HTML), with inconsistent units and trim/option naming. Real value only after the core recommendation loop is proven with seed data. |
| Vehicle comparison page | Additive on top of a working recommendation engine, not a prerequisite for demonstrating one. |
| Price history / versioning | Only matters once real pricelists arrive over time (promotions, model-year changes, currency). Not needed for a static seed dataset. |
| Object storage for original source documents | Follows directly from adding the ingestion pipeline — no source PDFs to store before that exists. |
| Voice interface | Listed as a bonus feature in the original spec. |
| Multi-language support | Listed as a bonus feature in the original spec. |
| Retrieval-Augmented Generation (RAG) | Useful once the catalog is large/unstructured or soft-criteria matching needs semantic similarity rather than rule-based scoring. Not needed while the catalog is small and hand-curated. |
| Sentiment analysis | Bonus feature; no clear MVP dependency. |
| Authentication | No user-specific state is required by the core scenario (single anonymous chat session → recommendation). |
| Analytics dashboard | Depends on real usage data accumulating post-launch. |
| CI/CD pipeline (beyond basic Docker Compose) | MVP uses Docker Compose for reproducibility; full CI/CD (GitHub Actions, automated deploys) is an operational maturity step for after the product is validated. |

## Database Design Changes for Version 2

Once the ingestion pipeline and price history are in scope, the schema evolves:

- **Raw staging layer**: an immutable staging table capturing each ingested source file's extracted rows (JSONB/text) before normalization, so extraction logic can be re-run against original data without re-scraping/re-uploading. Enables an audit trail for "why does this price look wrong."
- **Price as a fact table**: replace the single `price` column with `vehicle_prices (vehicle_id, trim, price, currency, valid_from, valid_to, source)` to support price history and trim-level variance. Add a denormalized `current_price` cache on the vehicle row (or a materialized view) to keep the common "show current price" query fast.
- **Original document storage**: store original PDFs/spreadsheets in object storage (MinIO for local/dev, S3-compatible for prod), with only a reference (path, checksum, upload date, parse status) in Postgres. Avoids backup bloat, buffer-cache pollution, and WAL growth that come from storing multi-MB blobs directly in Postgres (BYTEA/Large Objects). MinIO runs alongside Postgres in the same Docker Compose setup already used for MVP.
- **Vector search (if RAG is added)**: `pgvector` extension keeps embedding-based semantic search in the same Postgres instance rather than introducing a separate vector store — useful for soft-criteria matching ("suitable for gravel roads") that doesn't map to a structured filter.

## Sequencing Note

Recommended order once MVP is validated: (1) price history fact table → (2) raw staging + ingestion pipeline for one manufacturer as a proof of concept → (3) object storage for source documents → (4) comparison page → (5) remaining AI bonus features (RAG, voice, multi-language) based on what the demo/user feedback prioritizes.
