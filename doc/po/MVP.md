# Car Selector — MVP Scope

## Goal

Prove the end-to-end loop works: **chat → structured requirements → filtered/ranked results → explained recommendation.**
For a challenge/hackathon-style timebox, breadth of features matters less than a convincing, working core loop. Everything below earns its place either because it *is* that loop, or because it's cheap enough not to cost time needed elsewhere.

## Included Features

| Feature | Why |
|---|---|
| Chat interface, single-turn + basic follow-up | This is the core value proposition. Needs to work convincingly; doesn't need to handle every conversational edge case. |
| AI requirement extraction → structured JSON | The core "AI integration" the challenge is testing. One well-prompted LLM call (OpenAI/Azure OpenAI) is enough — no agents/tool-chaining needed. |
| Small, hand-curated vehicle catalog (~50–150 vehicles) | See [Data Approach](#data-approach) below — the pricelist ingestion pipeline is explicitly deferred. |
| SQL filter + simple weighted ranking (not RAG) | Structured filters (seats, body type, price ceiling, AWD) map directly to indexed SQL columns. A weighted score (soft-criteria matches + budget proximity) is simpler and more explainable than vector search — and explainability is a hard requirement. |
| Recommendation list with explanation text | Required by the spec's example output ("7 seats, large trunk, AWD available"). Cheap to generate from the same filter logic that produced the match. |
| Minimal vehicle detail view | Makes a recommendation feel actionable. Plain record dump — no galleries/rich media needed. |
| Docker Compose (Postgres + backend + frontend) | Near-zero cost, big payoff: reproducible demo/grading environment. Already in the recommended stack. |
| A handful of unit tests on extraction → filter → rank path | Cheap, and "Python development skills" / "system design" are explicit evaluation criteria — targeted tests signal rigor disproportionate to their cost. |

## Data Approach

Do **not** build the pricelist PDF ingestion pipeline for MVP. Parsing manufacturer pricelists (PDFs/spreadsheets, inconsistent per-brand formats) is an open-ended problem that can consume the entire timebox before anything is demoable.

Instead:
- Hand-seed a structured dataset (JSON/CSV import) covering ~50–150 vehicles.
- Vary the seed data across every field the recommendation engine filters on: body type, seat count, fuel type, AWD, price range — so the demo can showcase realistic recommendations across scenarios.
- Design the schema so it *can* absorb a future ingestion pipeline's output without rework (see below), even though the pipeline itself is out of scope.

## Database Design (MVP-relevant decisions)

- **Engine**: PostgreSQL, not SQLite — JSONB support is load-bearing even at MVP scope (see specs column below), and it avoids a later migration.
- **Schema shape**: relational core (brand, model, trim, price) + a `specs JSONB` column for long-tail attributes not common across all body types. Keeps the hot filter/sort columns indexable while staying flexible.
- **Price**: single current-price column is sufficient at MVP — no history/versioning table needed yet (see Version 2).
- **No file storage needed yet**: no PDFs are being ingested at MVP, so no object storage (MinIO/S3) setup is required.

## Explicitly Out of Scope for MVP

- Pricelist/car-parts PDF ingestion pipeline
- Vehicle comparison page
- Price history / versioning
- Object storage for original source documents
- Voice interface, multi-language support, RAG, sentiment analysis
- Authentication, analytics dashboard

See [Version2.md](./Version2.md) for these.
