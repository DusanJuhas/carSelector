"""Tests for CitroenParser on six real per-model price lists (downloaded
2026-11-02 from data.citroen.cz, valid from 1 October 2026 - see
scraper/tests/fixtures/citroen_*.pdf). Prices and row counts are
transcribed by hand from each table page's `page.extract_text()` output,
same discipline as test_mitsubishi_parser.py.

The fixtures are the real documents with every page except the cover and
the price table page(s) blanked and photos replaced by a 1x1 pixel (the
originals are 3-8 MB) - page numbers, text and the table's drawn rules
are unchanged, and the parser's output was checked to be identical on
the original and the reduced file for all six."""

from pathlib import Path

import pytest

from scraper.parsers.citroen import CitroenParser

FIXTURES = Path(__file__).parent / "fixtures"


def _fixture(name: str) -> Path:
    return FIXTURES / f"citroen_{name}_cenik.pdf"


def _variant(variants, trim: str, engine_fragment: str):
    return next(v for v in variants if v.trim == trim and engine_fragment in v.variant_name)


@pytest.mark.parametrize(
    ("name", "model", "count"),
    [
        ("c3", "C3", 13),
        ("c3_aircross", "C3 Aircross", 13),
        ("c4", "C4", 9),
        ("c4_x", "C4 X", 7),
        ("c5_aircross", "C5 Aircross", 10),
    ],
)
def test_citroen_parser_reads_every_row(name: str, model: str, count: int) -> None:
    variants = CitroenParser().parse(_fixture(name))
    assert len(variants) == count
    assert all(v.model == model for v in variants)
    assert all(v.currency == "CZK" and v.price for v in variants)


def test_citroen_parser_reads_c3_with_wrapped_electric_rows_and_merged_trims() -> None:
    variants = CitroenParser().parse(_fixture("c3"))
    # Mixed-case display font ("YoU", "CoLLECTIon") normalized to upper case.
    assert [v.trim for v in variants] == ["YOU"] * 3 + ["PLUS"] * 4 + ["COLLECTION"] * 3 + ["MAX"] * 3

    base = _variant(variants, "YOU", "Turbo 100k Manual")
    assert base.price == 420_000.0  # "Standardní cena", not the "Akční cena" 385 000
    assert base.powertrain == "ICE"
    assert base.source_page == 1

    # "Electric 113k Standard range Automatic" / price line / "(Baterie 30 kWh)"
    # are three printed lines, put back together into one row.
    ev = _variant(variants, "YOU", "Standard range")
    assert ev.variant_name == "C3 YOU Electric 113k Standard range Automatic (Baterie 30 kWh)"
    assert ev.price == 585_000.0
    assert ev.powertrain == "EV"

    assert _variant(variants, "MAX", "Hybrid 110k").powertrain == "MHEV"
    assert _variant(variants, "MAX", "Extended range").price == 725_000.0


def test_citroen_parser_assigns_three_row_groups_by_drawn_rules() -> None:
    # C3 Aircross MAX has 4 rows; its label sits between the 2nd and 3rd.
    variants = CitroenParser().parse(_fixture("c3_aircross"))
    max_rows = [v for v in variants if v.trim == "MAX"]
    assert [v.price for v in max_rows] == [585_000.0, 715_000.0, 785_000.0, 845_000.0]
    assert _variant(variants, "COLLECTION", "Extended range").price == 820_000.0


def test_citroen_parser_reads_c5_aircross_plug_in_hybrid_and_strips_footnotes() -> None:
    variants = CitroenParser().parse(_fixture("c5_aircross"))
    phev = _variant(variants, "PLUS", "Plug-in Hybrid 225k")
    assert phev.powertrain == "PHEV"
    assert phev.price == 1_025_000.0
    top = _variant(variants, "MAX", "Electric 230k")
    assert top.variant_name == "C5 Aircross MAX Electric 230k Extended range Automatic (97 kWh)"
    assert top.price == 1_215_000.0


def test_citroen_parser_reads_c4_x_seven_figure_price() -> None:
    variants = CitroenParser().parse(_fixture("c4_x"))
    assert _variant(variants, "MAX", "Electric 156k").price == 1_019_900.0


def test_citroen_parser_reads_both_berlingo_lengths() -> None:
    variants = CitroenParser().parse(_fixture("berlingo"))
    m = [v for v in variants if v.model == "Berlingo"]
    xl = [v for v in variants if v.model == "Berlingo XL"]
    assert len(m) == 10 and {v.source_page for v in m} == {1}
    assert len(xl) == 9 and {v.source_page for v in xl} == {2}
    assert _variant(m, "30 LET", "Diesel 130k Automatic").price == 790_000.0
    assert _variant(xl, "MAX", "Electric 136k").price == 1_105_000.0
    assert _variant(m, "PLUS", "Diesel 100k").powertrain == "ICE"
