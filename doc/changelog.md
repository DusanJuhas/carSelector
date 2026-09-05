# Changelog

All notable changes to DriveWise AI (car selector) are documented here, grouped
into versions reconstructed from the git history. Newest version first.

## Versioning scheme

Internal versions use `0.y.z`:

- The leading **`0`** is fixed for the whole pre-public-release phase. Public
  releases will start at `1.x.x`; the `0.` prefix is reserved so it never
  collides with those.
- **`y`** (major) increments on a *big* change — a technology switch or a
  fundamental shift in how the system is built (e.g. replacing the Node.js/
  React frontend with a pure-Python UI).
- **`z`** (minor) increments for everything else — new features, new scraper
  brands, refactors, fixes, and documentation.

There are no `x.y.z-alpha`/build-number suffixes; each entry below corresponds
to one or more related commits.

---

## 0.2.14 — 2026-09-06

### Fixed
- Infinite-scroll catalog browsing no longer disconnects the client once
  enough pages accumulate. Each scroll-triggered page load previously
  called `results.refresh()`, which (per `@ui.refreshable`'s "delete
  everything and recreate" semantics) re-rendered and re-sent *every*
  card loaded so far, not just the new page - at ~1.5 KB/card this
  crosses NiceGUI's ~1MB websocket message limit around 650-700
  accumulated cards, which the real catalog's 815 rows reliably hit,
  producing a "Message too long" popup followed by "Connection lost."
  `results_grid()` now returns its card container and a new
  `append_car_cards()` (`app/ui/components/results_grid.py`) appends only
  the newly-fetched page into it; `app/ui/pages.py`'s `on_results_scroll`
  uses this for the common case and falls back to a full
  `results.refresh()` only for the "Moje pořadí" custom-drag-order sort,
  whose `make_sortable` wiring is set up once per full render. Verified
  by scrolling the full 815-row catalog with no errors (previously
  reproducible around card ~700).

## 0.2.13 — 2026-09-06

### Added
- Guided step-by-step wizard as a non-technical alternative to the free-text
  chat, opened via a new "Průvodce výběrem" header button
  (`app/ui/components/wizard.py`, `WizardState` in `app/ui/state.py`). Ten
  questions (see `doc/ai/wizard-questions.md`) collect answers through
  buttons/number fields rather than typed text - each is phrased around the
  user's real-world situation (e.g. "Jezdíte i tam, kde bývá bláto, sníh
  nebo horší cesta?" instead of asking for a drivetrain) and mapped
  deterministically onto `StructuredRequirements`, so unlike the chat's
  `RequirementInterpreter` the wizard needs no AI call and works even
  without `ANTHROPIC_API_KEY` configured. `ConversationOrchestrator` gained
  `handle_wizard_answers`, sharing the same merge/recommend/explain pipeline
  as chat turns (`_apply_requirements`) so wizard- and chat-driven turns
  accumulate onto one conversation. `notes` is now shown in the
  requirements drawer (previously populated but never displayed).

## 0.2.12 — 2026-08-31

### Added
- Equipment surcharge prices are now captured and imported into the
  catalog. `skoda_equipment.py`'s parser already read the price column on
  Škoda's "Samostatné prvky výbavy" page but discarded it; the scraper's
  `EquipmentAssignment` gained `surcharge_amount`/`currency` columns to
  hold it, and `scripts/import_scraper_data.py` now imports
  STANDARD/OPTIONAL/NOT_AVAILABLE equipment rows into
  `option_items`/`option_availability` (PACKAGE rows, and OPTIONAL rows
  still missing a price, are skipped rather than fabricated - see that
  script's module docstring). Previously equipment/options were skipped
  entirely, since drivewise's `option_availability` CHECK constraint
  requires a price for every `optional` row and none was ever available.

## 0.2.11 — 2026-08-29

### Changed
- Catalog browsing now uses infinite scroll instead of a "Load more"
  button: scrolling the results column near its bottom fetches the next
  page automatically (`backend/app/ui/pages.py`'s `on_results_scroll`),
  with a small spinner shown while a page is in flight. The scroll
  container keeps using the browser's own `overflow-y-auto` scrollbar
  (not a virtualized list), so its thumb/track size stays accurate on its
  own as more cards are appended - no manual height bookkeeping needed.

## 0.2.10 — 2026-08-29

### Added
- BMW support in the scraper: discovery + parser for the brand's entire
  current lineup (29 model sections — combustion, electric, and plug-in
  hybrid — read generically from one combined price list rather than a
  hardcoded model list), with a PDF test fixture and parser tests
  (`scraper/monitors/discovery/bmw.py`, `scraper/parsers/bmw.py`).
- Wired BMW data into `scripts/import_scraper_data.py` so scraped results
  reach the catalog database.

### Fixed
- `scripts/import_scraper_data.py`'s `infer_drivetrain`/`infer_fuel_type`
  didn't recognize BMW's own AWD marker ("xDrive") or diesel suffix
  ("320d", fused onto the trim with no space, unlike other brands) —
  every BMW variant was defaulting to FWD/petrol regardless of its real
  drivetrain or fuel type.
- `powertrain_signature()` dedups "the same engine across trims" by
  stripping the trim label out of a variant's display name; for BMW the
  trim label already IS the row's entire distinguishing text (e.g.
  "320d"), so every row in a model collapsed onto one shared (and
  arbitrarily-classified) powertrain. `BmwParser` now folds
  displacement/power (and an explicit AWD marker for the few pairs that
  share an identical spec and differ only by xDrive) into the variant
  name so each row survives the stripping with its own distinct engine.

## 0.2.9 — 2026-08-29

### Added
- Mazda support in the scraper: discovery + parser for CX-5, 3 (hatchback
  and sedan), and CX-30, with PDF test fixtures and parser tests
  (`scraper/monitors/discovery/mazda.py`, `scraper/parsers/mazda.py`).
  Mazda's official price-list PDFs are an interactive-brochure export with
  duplicated/overlapping text layers, unlike any other brand's plain price
  tables — the parser's module docstring documents the extraction
  technique this needed (font-size filtering, off-page-content filtering,
  exact-position row grouping, and strict per-row column validation that
  silently drops a malformed row rather than risk extracting a wrong
  price).
- Wired Mazda data into `scripts/import_scraper_data.py` so scraped
  results reach the catalog database.

### Fixed
- The Mazda entry in `scraper/config/sources.yaml` listed model `3`
  unquoted, so YAML parsed it as the integer `3` instead of the string
  `"3"` — silently breaking the discoverer's model-matching for that one
  model (it compared against string captions and never matched an int).
  Caught by cross-checking the discoverer's live output against the
  configured model list before considering the source done.

## 0.2.8 — 2026-08-29

### Fixed
- The catalog-browsing header ("N vozů v katalogu") was built from
  `len(cars)` — the currently loaded page of results (capped at
  `page_size`, 20 by default) — rather than the real total, so it never
  read as more than the first page's size regardless of how many vehicles
  actually matched. Now uses `catalog_state.total`, the real count already
  returned by the backend on every page load (`backend/app/ui/pages.py`).

## 0.2.7 — 2026-08-29

### Added
- Mercedes-Benz support in the scraper: discovery + parser for C-Class and
  E-Class (sedan and estate body styles), reading the combined "Souhrnný
  ceník" PDF that covers the brand's entire lineup, with a PDF test fixture
  and parser tests (`scraper/monitors/discovery/mercedes_benz.py`,
  `scraper/parsers/mercedes_benz.py`).
- Wired Mercedes-Benz data into `scripts/import_scraper_data.py` so scraped
  results reach the catalog database.

### Fixed
- `scripts/import_scraper_data.py` assumed every scraper document covers
  exactly one model; Mercedes-Benz's combined price list broke that
  assumption (all its variants were being imported under a single model).
  Variants are now grouped by their own `model` value within a document,
  and `SourceDocument` rows are keyed by `(file_path, model)` instead of
  `file_path` alone, so one PDF can correctly back several models.

## 0.2.6 — 2026-08-29

### Added
- Hyundai support in the scraper: discovery + parser for i20, i30, Kona,
  Tucson (ICE and HEV/PHEV) and Santa Fe, with PDF test fixtures and parser
  tests (`scraper/monitors/discovery/hyundai.py`, `scraper/parsers/hyundai.py`).
- Wired Hyundai data into `scripts/import_scraper_data.py` so scraped results
  reach the catalog database.

## 0.2.5 — 2026-08-29

### Added
- `doc/carVendors.md` documenting the supported car vendors/brands.
- Catalog filter controls: a filter bar component in the NiceGUI UI, backing
  query parameters in the vehicles API, and matching state handling and tests.

## 0.2.4 — 2026-08-26

### Fixed
- Locale bug in `backend/app/ui/i18n.py`.

## 0.2.3 — 2026-08-26

### Added
- Pluggable LLM client abstraction (`backend/app/ai/llm.py`) with Groq as an
  additional provider alongside the existing one, plus config and tests.

## 0.2.2 — 2026-08-26

### Added
- Admin console page (`backend/app/ui/admin.py`) for backend administration,
  linked from the header.

(Merge of pull request #2, bringing in the NiceGUI migration branch.)

## 0.2.1 — 2026-08-25 / 2026-08-26

### Added
- `scripts/run.bat` to launch the unified backend+UI app.

### Fixed
- A rendering glitch in the NiceGUI pages module.

## 0.2.0 — 2026-08-25

### Changed — **Major: migration to NiceGUI, Node.js removed**
- Replaced the separate React/TypeScript/Vite frontend with a Python
  NiceGUI UI served directly by the FastAPI backend: chat column, header,
  requirements drawer, results grid, vehicle detail modal, sorting and i18n
  were all reimplemented under `backend/app/ui/`.
- Deleted the entire `frontend/` tree (React components, npm/Vite tooling,
  `package-lock.json`, TypeScript config) — the project is now a single
  Python stack end-to-end, run via `pyproject.toml` / `requirements.txt`.
- This is the dividing line between the `0.1.x` (polyglot: Node.js + Python)
  and `0.2.x` (pure Python) eras of the project.

---

## 0.1.24 — 2026-08-25

### Added
- `doc/db/natural_language_requests.md`: design proposal for translating
  free-text user requirements into structured technical car parameters.

## 0.1.23 — 2026-08-22

### Added
- `doc/db/drivewise-schema.png` database schema diagram.
- `doc/implemented_overview.md` summarizing the current state of the
  implementation, plus UI screenshots (`doc/gui/car_detail.jpg`,
  `doc/gui/main_screen.jpg`).

## 0.1.22 — 2026-08-16

### Added
- Sorting for the results grid: `SortControl` component, `useCustomOrder`
  hook, `sortCars` utility, and a backing `sort` query parameter on the
  vehicles API.

## 0.1.21 — 2026-08-16

### Added
- Vehicle detail modal shown on car-card click, with a dedicated API client
  (`vehicleDetail.ts`) and `useVehicleDetail` hook.

## 0.1.20 — 2026-08-15

### Changed
- Replaced frontend mock conversation data with real API clients
  (`api/catalog.ts`, `api/client.ts`, `api/conversation.ts`,
  `api/vehicleSummary.ts`) and matching hooks/stores, wiring the chat UI to
  live backend vehicle data for the first time.

## 0.1.19 — 2026-08-15

### Changed
- Strengthened the Claude Code skills to generate more consistent
  object-oriented code, and introduced a documentation rule requiring
  docstrings on all methods and parameters — applied across the backend
  (AI, services) and scraper (parsers, discovery, downloader) modules.

## 0.1.18 — 2026-08-15

### Added
- `scripts/import_scraper_data.py`: imports parsed scraper output into the
  backend catalog database.
- Alembic migration adding a "hybrid" fuel type.

## 0.1.17 — 2026-08-15

### Changed
- Moved `scraper.db` and downloaded price-list PDFs out of
  `scraper/storage/` into a shared top-level `storage/` directory used by
  both the scraper and the backend, with a new `storage/README.md`.

## 0.1.16 — 2026-08-15

### Changed
- Consolidated the separate `backend/requirements*.txt` and
  `scraper/requirements.txt` into unified root-level `requirements.txt` /
  `requirements-dev.txt`.

## 0.1.15 — 2026-08-15

### Added
- SQLite-backed catalog storage: a database seed script
  (`backend/app/db/seed.py`) and refined SQLAlchemy models/config.

## 0.1.14 — 2026-08-15

### Changed
- Switched the frontend's default locale from Czech to English; added an
  i18n config with separate `cs`/`en` translation files.

## 0.1.13 — 2026-08-15

### Changed
- Restructured project documentation: overhauled the root `README.md` and
  added `doc/README.md` as an index; trimmed and reorganized `roles.md` and
  updated the Claude skill docs and architecture/implementation-plan docs.

## 0.1.12 — 2026-08-14

### Added
- `doc/ai/claude-integration-brainstorm.md` exploring approaches for Claude
  API integration.
- Standalone scripts to run just the Vite frontend dev server
  (`scripts/run-ui.{bat,ps1,sh}`) plus a `.claude/launch.json` entry.

## 0.1.11 — 2026-08-13

### Added
- 8 additional OEM price lists registered in the scraper source config.
- Kia support: discovery + parser + test fixtures.
- Toyota support: discovery + parser + test fixtures.

## 0.1.10 — 2026-08-12 / 2026-08-13

### Added
- `doc/db/db-structure.md` notes and a detailed proposed database structure.
- `doc/po/MVP.md` and `doc/po/Version2.md` roadmap/scope documents.

## 0.1.9 — 2026-08-03

### Added
- Downloaded price-list PDFs and a local `scraper.db` snapshot committed
  into `scraper/storage/` for reproducible local development.
- Merged pull request #1 (`fb_webScraping` branch).

## 0.1.8 — 2026-07-20

### Added
- Backend AI layer: `requirement_interpreter.py` and
  `explanation_generator.py`.
- REST API endpoints for brands, conversations, models and vehicles.
- Service layer: `catalog.py`, `conversation.py`, `recommendation_engine.py`.
- Initial backend test suite (`tests/test_catalog_api.py`, `conftest.py`).

## 0.1.7 — 2026-07-20

### Added
- FastAPI backend scaffold: Alembic migrations, SQLAlchemy models for the
  catalog schema (brand, car model, trim, powertrain, configuration, color,
  option item/availability, price, source document) and `doc/api-contract.md`.

## 0.1.6 — 2026-07-20

### Added
- Claude Code skill definitions for the project's architecture, data model,
  scraper, and AI-recommendation domains (`.claude/skills/`).
- Sample OEM PDF price lists (Mazda CX-5, VW Tiguan) for scraper development.

## 0.1.5 — 2026-07-19

### Added
- Python web scraper service (`scraper/`): source discovery, PDF
  downloading, per-brand parsers, SQLite-backed models/repositories, and
  test fixtures/tests for Škoda and Volkswagen (ICE + EV) price lists.
- `scraper/README.md`.

## 0.1.4 — 2026-07-19

### Added
- `doc/main.md` and `doc/roles/roles.md` (team roles), followed by a
  formatting cleanup pass.

## 0.1.3 — 2026-07-18

### Added
- React + TypeScript + Vite frontend scaffold: chat column, results grid,
  car card, requirements drawer, app header components with mock
  conversation data, component tests, and tooling (`oxlint`, `tsconfig`).

## 0.1.2 — 2026-07-16

### Added
- `doc/prompt/CLAUDE.md` project rules for Claude Code.
- Graphical UI design proposals (HTML/PDF concept mockups) under `doc/gui/`.

## 0.1.1 — 2026-07-09

### Added
- `doc/arch/webScraping/Car_Price_List_Architecture.md` describing the
  web-scraping architecture.

### Changed
- Consolidated `arch/` and `prompt/` folders under `doc/`.

## 0.1.0 — 2026-07-01

### Added
- Initial commit (`.gitignore`, `README.md`).
- First three drafts of the system architecture (`arch/architecture.md`,
  `Car_Selector_Architecture.drawio`/`.jpg`).
