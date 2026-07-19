---
name: drivewise-architecture
description: The system architecture, technology stack, and layer responsibilities for the DriveWise AI car-selection platform. Use this whenever working on DriveWise AI to understand where a piece of functionality belongs, which layer owns it, how data flows end to end, or which technology to reach for. Consult it before adding a new module, wiring a new endpoint, choosing a library, or deciding whether logic goes in the frontend, backend, AI layer, data layer, or scraper — even if the request doesn't say "architecture" explicitly.
---

# DriveWise AI — Architecture

DriveWise AI helps users find suitable vehicles based on their requirements, preferences, and budget. Users chat through a web interface; the backend combines AI-powered requirement analysis with vehicle data in a central database.

## Source of truth

This skill is the map, not the law. When it conflicts with the repo, the repo wins in this order:
1. `CLAUDE.md` — locked conventions (stack versions, style, structure)
2. `docs/api-contract.md` — endpoint signatures and shared schemas
3. This skill — high-level architecture and layer responsibilities

If you change a layer boundary or add a component, update this skill so it stays trustworthy.

## Layers and who owns what

Keep responsibilities on the correct side of the frontend/backend boundary. When unsure where logic belongs, match it to the owning layer below.

**Frontend** — presentation only. Car-selection wizard, chat interface, search/filtering, recommendation and comparison display, vehicle detail pages. Talks to the backend over REST/HTTPS. No business logic, no ranking, no direct DB or AI calls.

**Backend (FastAPI)** — the brain. Exposes REST endpoints, validates requests, runs business logic and the recommendation engine, orchestrates calls to the AI layer and the database. All ranking and filtering lives here.

**AI layer** — natural-language understanding. Turns free-text user needs into structured search parameters, detects intent, asks follow-up questions, and generates human-readable explanations for recommendations. Called *by* the backend; never called directly from the frontend.

**Data layer (PostgreSQL)** — the vehicle catalog: specs, pricing, features. See `drivewise-data-model` for the schema and ORM conventions.

**Scraper** — a separate Python service that collects vehicle data from external sources and writes cleaned records into PostgreSQL. See `drivewise-scraper`.

## End-to-end flow

```
User → Frontend (React) → FastAPI backend
                              ├─→ AI layer      (extract structured requirements, explain results)
                              └─→ PostgreSQL     (fetch candidate vehicles)
                                     ↑
                              Recommendation engine (filter + rank in the backend)
                                     ↑
                              Scraper (populates the catalog, offline)
```

The scraper runs independently of the request path — it populates the catalog ahead of time, so user requests never wait on scraping.

## Technology stack

Defer to `CLAUDE.md` for exact versions; this is the intended shape.

- **Backend:** Python 3.11+, FastAPI, SQLAlchemy, Pydantic
- **Frontend:** React + TypeScript (Vue is an acceptable alternative if the repo uses it), Axios for HTTP
- **Database:** PostgreSQL (SQLite is acceptable only for a throwaway prototype)
- **AI:** Claude API for requirement extraction and explanations (OpenAI / Azure OpenAI / LangChain / Ollama are alternatives the project may use)
- **Scraping:** BeautifulSoup, Scrapy, or Playwright
- **DevOps:** Docker, GitHub Actions, unit tests

## Design principles to preserve

- Clean separation between frontend and backend — the frontend is a thin client.
- Microservice-ready: the scraper is decoupled and can scale independently.
- AI assists requirement gathering; it does not own ranking decisions.
- Centralized PostgreSQL storage; deployable to Azure, AWS, or Kubernetes.

## Bonus / stretch features

Voice interface, sentiment analysis, personalized recommendations, RAG, multi-language support, auth, analytics dashboard, and Swagger/OpenAPI docs are planned extras. Build them as additive modules that respect the layer boundaries above — e.g. RAG belongs in the AI layer, auth in the backend, analytics as its own concern.
