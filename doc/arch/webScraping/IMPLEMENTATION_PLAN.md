# Implementation plan — scoped-down phase 1

A companion to `Car_Price_List_Architecture.md`. That document describes
the target architecture (10 OEMs, Postgres, Docker, OCR, APScheduler,
LLM parsing). Before we get there, we need to verify the pipeline
actually works on real data — so this plan scopes the first step down to
a single brand.

## Why a vertical slice, not the whole architecture at once

OEM price lists differ significantly in format (table vs. running text
vs. image-based PDF). Without verifying against a real PDF, any
universal parser is just a guess. Goal of phase 1: an end-to-end pass
(download → parse → store → verify) for a single brand, before investing
in a plugin architecture for ten more.

## Phase 1 — Škoda pilot

1. Find the real Škoda CZ page with the current price list and determine
   the actual PDF format (table/text/image). Fill in
   `scraper/config/sources.yaml` (source_url, pdf_pattern).
2. Write the part of `scraper/monitors/source_monitor.py` that finds the
   specific PDF link on the page (requests+BeautifulSoup, or Playwright
   if the page is JS-rendered).
3. Write `scraper/parsers/skoda.py` to match the actual PDF structure.
4. Verify via `scraper/verification/review_cli.py` — manually check the
   price/equipment for a few variants against the open PDF.
5. Once the data is verified, run `scraper/main.py` against the full
   current price list and spot-check the output again.

## Phase 2 — second brand + refactor into a plugin pattern

Once phase 1 checks out, add a second brand (Volkswagen or Toyota) and
only then confirm/adjust the `BaseParser` interface based on what
repeats between two real implementations.

## Phase 3 — remaining OEMs from the roadmap

Hyundai, Kia, and others per `Car_Price_List_Architecture.md`. Each
brand = a new file in `scraper/parsers/` + a line in `sources.yaml`,
without touching other brands' parsers — this lets different people work
on different brands in parallel.

## Phase 4 — move to production infrastructure

Switch `SCRAPER_DATABASE_URL` from SQLite to Postgres, introduce Alembic
migrations, add APScheduler for periodic runs, stand up the FastAPI
reporting layer (`GET /variants`, `/price-history`, ...), and merge
`scraper/` into the main `carSelector` repo.

## Data verification — a principle across all phases

Every `Variant` and `PriceHistory` record in the DB carries
`document_id`, `source_page`, and `raw_text` (see
`scraper/database/models.py`). This is intentional: an extracted value
can always be traced back to the exact page and text in the source PDF
via `review_cli.py`, instead of trusting the parser blindly.
