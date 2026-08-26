---
name: drivewise-architecture
description: The system architecture, technology stack, and layer responsibilities for the DriveWise AI car-selection platform. Use this whenever working on DriveWise AI to understand where a piece of functionality belongs, which layer owns it, how data flows end to end, or which technology to reach for. Consult it before adding a new module, wiring a new endpoint, choosing a library, or deciding whether logic goes in the frontend, backend, AI layer, data layer, or scraper — even if the request doesn't say "architecture" explicitly.
---

# DriveWise AI — Architecture

DriveWise AI helps users find suitable vehicles based on their requirements, preferences, and budget. Users chat through a web interface; the backend combines AI-powered requirement analysis with vehicle data in a central database.

## Source of truth

This skill is the map, not the law. When it conflicts with the repo, the repo wins in this order:
1. `doc/prompt/CLAUDE.md` — locked conventions (stack versions, style, structure)
2. `doc/api-contract.md` — endpoint signatures and shared schemas
3. This skill — high-level architecture and layer responsibilities

If you change a layer boundary or add a component, update this skill so it stays trustworthy.

## Layers and who owns what

Keep responsibilities on the correct side of the frontend/backend boundary. When unsure where logic belongs, match it to the owning layer below.

**UI** (`backend/app/ui/`) — presentation only. Car-selection chat interface, search/filtering, recommendation display, vehicle detail pages. NiceGUI, mounted directly onto the same FastAPI process (`ui.run_with`, see `app/main.py`) — calls the service layer in-process rather than over HTTP, but the responsibility boundary is the same as if it were a separate client: no business logic, no ranking, no direct AI calls (DB access is via the service layer's own functions, not raw queries in the UI layer).

**Backend (FastAPI)** — the brain. Exposes REST endpoints, validates requests, runs business logic and the recommendation engine, orchestrates calls to the AI layer and the database. All ranking and filtering lives here.

**AI layer** — natural-language understanding. Turns free-text user needs into structured search parameters, detects intent, asks follow-up questions, and generates human-readable explanations for recommendations. Called *by* the backend; never called directly from the frontend.

**Data layer (PostgreSQL)** — the vehicle catalog: specs, pricing, features. See `drivewise-data-model` for the schema and ORM conventions.

**Scraper** — a separate Python service that collects vehicle data from external sources and writes cleaned records into PostgreSQL. See `drivewise-scraper`.

## End-to-end flow

```
User → UI (NiceGUI, same process as the FastAPI backend) → service layer (in-process calls)
                              ├─→ AI layer      (extract structured requirements, explain results)
                              └─→ PostgreSQL     (fetch candidate vehicles)
                                     ↑
                              Recommendation engine (filter + rank in the backend)
                                     ↑
                              Scraper (populates the catalog, offline)
```

The REST API (`app/api/*`, prefix `/api`) still exists on the same FastAPI app for any external
client (see `doc/api-contract.md`) - the UI just doesn't have to go through it, since it's not a
separate process anymore.

The scraper runs independently of the request path — it populates the catalog ahead of time, so user requests never wait on scraping.

## Technology stack

Locked per `doc/prompt/CLAUDE.md` — do not swap these without discussion.

- **Backend:** Python 3.11+, FastAPI, SQLAlchemy, Pydantic v2, PostgreSQL (Alembic for migrations)
- **UI:** NiceGUI (Python), mounted onto the same FastAPI app - no Node.js/npm anywhere in the
  repo. Styled with Tailwind utility classes (NiceGUI ships Tailwind support built in). Tested with
  pytest (`backend/tests/ui/`), not a browser-based JS test runner.
- **AI:** Claude API (Anthropic SDK, default) or Groq, selected via `AI_PROVIDER` - both behind one
  `LlmClient` interface (`app/ai/llm.py`); called exclusively from `backend/app/ai`
- **Scraping:** the standalone `scraper/` service — requests/BeautifulSoup/pdfplumber today, see `doc/arch/webScraping/` for the target/phased stack
- **DevOps:** Docker, GitHub Actions, unit tests (aspirational — not yet set up)

## Code style: OOP + fully-documented methods

Applies uniformly across the whole Python codebase - backend, AI layer, scraper, and the UI layer
(`app/ui/`, formerly a React frontend with its own JS-specific conventions; now that it's Python
too, there's no separate carve-out for it).

- **Prefer classes for anything with real behavior grouped around state or a clear
  responsibility** — a service, an engine, a parser, a repository, a client wrapper. This is
  already how the data layer (SQLAlchemy/Pydantic classes, see `drivewise-data-model`) and the
  scraper (`BaseParser`/`BaseDiscoverer` plugin classes, see `drivewise-scraper`) work — extend
  that pattern rather than adding free-floating functions next to it (see
  `drivewise-ai-recommendations`'s Code style section for how this applies to the requirement
  interpreter, recommendation engine, and explanation generator). Small, stateless,
  single-purpose helpers (a pure formatting function, a regex extractor) don't need a class just
  to have one.
- **Every method and function gets a docstring that documents its parameters and return value**,
  not just a one-line summary. Google-style `Args:`/`Returns:`/`Raises:` sections, e.g.:

  ```python
  def recommend(self, requirements: StructuredRequirements, *, limit: int = 10) -> list[VehicleSummary]:
      """Filters the catalog on hard constraints, then scores and ranks the rest.

      Hard constraints (body_type, budget, fuel_type) are pushed down to the catalog query;
      soft preferences (drivetrain, priorities, budget headroom) are scored here - see the
      module docstring for why drivetrain is soft, not hard.

      Args:
          requirements: Structured output of the AI requirement interpreter.
          limit: Maximum number of ranked results to return.

      Returns:
          Vehicles ranked best-first, each with `match_score` set and the top result flagged
          `top_pick=True`.
      """
  ```

  Keep the project's existing "explain the WHY, not the WHAT" habit for any prose above the
  `Args:`/`Returns:` block — identifiers already say what a parameter is called; the docstring
  earns its place by adding what a signature can't (a non-obvious constraint, why a default is
  what it is, a design tradeoff), not by restating the type.
- This doesn't mean forcing classes onto the UI layer's small render functions (`app/ui/components/
  *.py`'s `header()`, `car_card()`, etc.) - those are exactly the "small, stateless, single-purpose
  helpers" the bullet above already exempts, same as `sort_cars`/`format_money`. What does need a
  class there is anything with real per-connection state: `ConversationState`/`CatalogState`
  (`app/ui/state.py`) are dataclasses with behavior, the same pattern as `_ConversationState` in
  `app/services/conversation.py`.

## Design principles to preserve

- Clean separation between the UI layer and the service layer it calls — the UI is a thin
  presentation layer, even though it's no longer a separate process.
- Microservice-ready: the scraper is decoupled and can scale independently.
- AI assists requirement gathering; it does not own ranking decisions.
- Centralized PostgreSQL storage; deployable to Azure, AWS, or Kubernetes.

## Bonus / stretch features

Voice interface, sentiment analysis, personalized recommendations, RAG, multi-language support, auth, analytics dashboard, and Swagger/OpenAPI docs are planned extras. Build them as additive modules that respect the layer boundaries above — e.g. RAG belongs in the AI layer, auth in the backend, analytics as its own concern.
