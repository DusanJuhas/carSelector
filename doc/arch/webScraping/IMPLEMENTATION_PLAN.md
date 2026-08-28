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

---

## Current status (as of 2026-08)

`scraper/` already lives inside this repo (it is no longer a separate local
copy pending merge — see the note at the top of `scraper/README.md` for how
that framing changed). This section is the living record of coverage and
next steps; update it in the same change as any parser/discoverer addition.

### Data coverage

| Brand | Model | Powertrain |
|---|---|---|
| Škoda | Fabia, Scala, Kamiq, Octavia, Karoq, Kodiaq, Superb | ICE |
| Škoda | Enyaq, Elroq, Epiq, Peaq | EV |
| Volkswagen | Golf, Golf Variant, Passat, Polo, T-Cross, T-Roc, Taigo, Tayron, Tiguan, Touran | ICE / MHEV / PHEV |
| Volkswagen | ID.3 Neo, ID.4, ID.7, ID.7 Tourer, ID. Polo | EV |
| Kia | Ceed SW, Niro, Sportage | ICE / MHEV / HEV / PHEV |
| Toyota | Yaris, Yaris Cross, Corolla Sedan, Corolla Hatchback, Corolla Touring Sports, C-HR, RAV4 | HEV / PHEV |
| Hyundai | i20, i30, Kona, Tucson, Santa Fe | ICE / MHEV / HEV / PHEV |

Every variant has a price, a trim level, and a link back to the page/exact
text in the source PDF (`raw_text`), so it can always be verified against
the source. Škoda additionally includes optional equipment (the
"Samostatné prvky výbavy" / standalone equipment items page — other
equipment formats, VW/Kia/Toyota equipment, and other OEMs are listed
under Status and next steps below). Kia's Sportage and Toyota's Corolla
both have more than one source document per model (Sportage: ICE vs.
HEV/PHEV; Corolla: Sedan/Hatchback/Touring Sports body styles) — all are
discovered and parsed the same way, see `parsers/kia.py`/
`monitors/discovery/kia.py` and `parsers/toyota.py`/
`monitors/discovery/toyota.py`. Hyundai's Tucson likewise has two source
documents (ICE/MHEV vs. HEV/PHEV, a separate PDF each), and its Santa Fe
has HEV and PHEV tables on different pages of the SAME document — both
handled by one `parsers/hyundai.py`/`monitors/discovery/hyundai.py` pair,
see that parser's module docstring for its word-position technique
(Hyundai's price table has 3-4 numeric columns per row, more than Škoda's
positional reconstruction needed to handle). Kia, Toyota, and Hyundai
price lists don't carry a release date `extract_release_date` understands
(Kia: a closed monthly validity range; Toyota: "Ceník platí od"; Hyundai:
"Ceník osobních vozů platný od D. <written-out month> RRRR" — none match
Škoda/VW's open-ended, numeric-month "Platnost od D. M. RRRR"), so their
variants currently have `valid_from` = download date rather than the
price list's own effective date.

### Status and next steps

Done: OOP architecture (class + plugin registry for both parsers and
discoverers), Škoda and VW complete (both ICE and EV), Kia price lists
(Ceed SW/Niro/Sportage, ICE/MHEV/HEV/PHEV), Toyota price lists (Yaris,
Yaris Cross, Corolla x3 body styles, C-HR, RAV4, HEV/PHEV), Hyundai price
lists (i20, i30, Kona, Tucson, Santa Fe, ICE/MHEV/HEV/PHEV), optional
equipment for Škoda (one of three formats — "Samostatné prvky výbavy" /
standalone equipment items).

Remaining: Škoda "Pakety" (packages) and per-trim standard equipment
(the other two equipment formats), VW/Kia/Toyota/Hyundai equipment,
Kia/Toyota/Hyundai release-date extraction (see Data coverage above),
Dacia/Mercedes-Benz/Ford/Renault/BMW, and the rest of `doc/carVendors.md`'s
"Mainstream brands" list beyond the original top-10-by-CZ-market-share
scope (Peugeot, BMW, MG, Cupra, Opel, Citroën, Audi, Seat, Volvo, Suzuki,
Mazda, Nissan, Honda, Mitsubishi, Fiat, ...). Details and the reasoning for
scaling one piece at a time (vertical slice, verify on real data, then
generalize) are in the phases above.

There's now a manual/periodic import step from this scraper's database
(`storage/scraper.db`, repo root — see `storage/README.md`) into the
backend's normalized catalog schema (`backend/app/models/`):
`scripts/import_scraper_data.py`. It's not a live pipeline (nothing
triggers it automatically after a scrape) and not a complete mapping -
equipment/options aren't imported (no surcharge data in the source to
satisfy the schema's constraint), and fuel_type/drivetrain are inferred
from free-text variant names rather than a structured field. See that
script's module docstring for the full list of what it does and doesn't
carry over, and `drivewise-data-model` for how it fits the rest of the
data model.
