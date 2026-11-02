"""Parser for SEAT's per-model "Ceník" price lists (verified against real
PDFs downloaded 2026-11-02 from seat.cz's own /dam/files/ asset store,
effective 1-5 October 2026 - see scraper/tests/fixtures/seat_*.pdf).
Covers Ibiza, Arona, Leon and Leon Sportstourer - every current SEAT
nameplate with a price list of its own (Ateca is sold stock-only: its
page links a "Katalog" but no "Ceník", see discovery/seat.py).

SEAT and CUPRA share one Czech importer and, verified page by page, one
price-list template: the same "CENÍK" page
(a trim heading, then one row per engine - engine, power "kW/k",
transmission, WLTP consumption, CO2, "Cena s DPH"), the same "SÉRIOVÁ
VÝBAVA" newspaper-grid equipment pages with "<TRIM> /navíc oproti výbavě
<OTHER>" delta headings, and the same "BARVY" page with per-trim mark
glyphs. So `SeatParser` is `CupraParser` with only its brand and its own
list of model names swapped - the row regex, powertrain classification
(eTSI -> MHEV, e-HYBRID -> PHEV), equipment and colour extraction are
reused as-is rather than copied. See parsers/cupra.py's and
parsers/cupra_equipment.py's own module docstrings for the details.

Known gap, in SEAT's own source rather than the parser: the "Akční model
COPA" special edition (a single price row on Leon/Leon Sportstourer) has
no "SÉRIOVÁ VÝBAVA" section of its own in those two documents, so it only
gets its colours - the same situation as CUPRA Raval's "Akční model
ROOKIE". Arona's and Ibiza's own documents DO describe COPA (as "Akční
model COPA /navíc oproti výbavě Style"), so it's fully populated there.

Like CUPRA, the "Platnost od ..." date sits on the price page (page 2),
not the cover page `_pdf_layout.extract_release_date` reads, so
`release_date` stays None and VariantRepository falls back to the
download date."""

from __future__ import annotations

from .cupra import CupraParser

# Longest name first, so "Leon Sportstourer"'s cover page isn't misread as plain "Leon".
_KNOWN_MODELS = ("Leon Sportstourer", "Leon", "Ibiza", "Arona")


class SeatParser(CupraParser):
    brand = "seat"
    known_models = _KNOWN_MODELS
