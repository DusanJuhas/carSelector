"""Tests for SeatParser on all four real per-model price lists (downloaded
2026-11-02 from seat.cz, effective 1-5 October 2026 - see scraper/tests/
fixtures/seat_*.pdf). Prices are transcribed by hand from the PDFs' own
"CENÍK" page text, same discipline as test_cupra_parser.py.

The fixtures are the real documents with every page the parser doesn't
read (optional-equipment, technical-data, dimension pages) blanked and
photos replaced by a 1x1 pixel, to keep them small (the originals are
4-35 MB) - page numbers, text and vector layout are unchanged, and the
parser's output was checked to be identical on the original and the
reduced file for all four."""

import re
from pathlib import Path

from scraper.parsers.seat import SeatParser

FIXTURES = Path(__file__).parent / "fixtures"
IBIZA = FIXTURES / "seat_ibiza_cenik.pdf"
ARONA = FIXTURES / "seat_arona_cenik.pdf"
LEON = FIXTURES / "seat_leon_cenik.pdf"
LEON_SPORTSTOURER = FIXTURES / "seat_leon_sportstourer_cenik.pdf"


def _variant(variants, trim: str, engine_fragment: str):
    return next(v for v in variants if v.trim == trim and engine_fragment in v.variant_name)


def test_seat_parser_extracts_leon_variants_with_hybrid_powertrains() -> None:
    # Akční model COPA (1) + Style (7) + FR (7) = 15.
    variants = SeatParser().parse(LEON)
    assert len(variants) == 15
    assert all(v.model == "Leon" for v in variants)
    assert all(v.currency == "CZK" for v in variants)
    assert {v.trim for v in variants} == {"Akční model COPA", "Style", "FR"}

    base = _variant(variants, "Style", "1.5 TSI 115k")
    assert base.price == 584_900.0
    assert base.powertrain == "ICE"
    assert base.source_page == 2

    assert _variant(variants, "FR", "1.5 eTSI 150k DSG").powertrain == "MHEV"
    phev = _variant(variants, "FR", "e-HYBRID 204k DSG")
    assert phev.powertrain == "PHEV"
    assert phev.price == 919_900.0


def test_seat_parser_tells_leon_sportstourer_apart_from_leon() -> None:
    variants = SeatParser().parse(LEON_SPORTSTOURER)
    assert len(variants) == 15
    assert all(v.model == "Leon Sportstourer" for v in variants)
    assert _variant(variants, "Akční model COPA", "1.5 TSI 115k").price == 544_900.0


def test_seat_parser_extracts_ibiza_and_arona() -> None:
    ibiza = SeatParser().parse(IBIZA)
    assert len(ibiza) == 11
    assert all(v.model == "Ibiza" for v in ibiza)
    assert _variant(ibiza, "Reference", "1.0 MPI 80k").price == 409_900.0
    assert _variant(ibiza, "FR", "1.5 TSI 150k DSG").price == 624_900.0

    arona = SeatParser().parse(ARONA)
    assert len(arona) == 9
    assert all(v.model == "Arona" for v in arona)
    assert all(v.powertrain == "ICE" for v in arona)
    assert _variant(arona, "Style", "1.0. TSI 115k DSG").price == 599_900.0


def test_seat_parser_reads_standard_equipment_and_colors() -> None:
    # Reused CUPRA equipment extraction: Arona's FR is "FR /navíc oproti
    # výbavě Style" in the source, so it must include Style's items too.
    arona = SeatParser().parse(ARONA)
    style = _variant(arona, "Style", "1.0. TSI 95k")
    fr = _variant(arona, "FR", "1.0. TSI 95k")
    assert "SEAT Drive Profile" in fr.equipment
    # Colours ("Glacial bílá - 2Y2Y") are offered per trim, so only the
    # standard-equipment items must carry over.
    style_items = {k for k in style.equipment if not re.search(r" - [A-Z0-9]{4}$", k)}
    assert style_items
    assert style_items <= set(fr.equipment)

    # Leon's own document has no SÉRIOVÁ VÝBAVA section for its COPA
    # special edition (a gap in SEAT's source, like CUPRA Raval's ROOKIE)
    # - only its colours are known, far fewer items than a real trim.
    leon = SeatParser().parse(LEON)
    copa = _variant(leon, "Akční model COPA", "1.5 TSI 115k")
    assert 0 < len(copa.equipment) < len(_variant(leon, "Style", "1.5 TSI 115k").equipment)


def test_seat_parser_raw_text_traceable_to_source() -> None:
    variant = _variant(SeatParser().parse(IBIZA), "Akční model COPA", "1.0 MPI 80k")
    assert "399 900 Kč" in variant.raw_text
    assert variant.source_page == 2
