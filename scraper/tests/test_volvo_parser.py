"""Tests for VolvoParser on all ten real per-model price lists (downloaded
2026-11-02 from volvodirect.cz, effective 1 Feb-15 Sep 2026 depending on
model - see scraper/tests/fixtures/volvo_*.pdf). Prices and cell counts
are transcribed by hand from each document's own price-matrix page text
("-" cells counted out), same discipline as test_ford_parser.py.

The fixtures are the real documents with every page except the cover and
the price matrix page(s) blanked and photos removed (the originals are
3.5-6.6 MB) - page numbers, text and vector layout are unchanged, and the
parser's output was checked to be identical on the original and the
reduced file for all ten."""

from pathlib import Path

import pytest

from scraper.parsers.volvo import VolvoParser

FIXTURES = Path(__file__).parent / "fixtures"


def _fixture(model: str) -> Path:
    return FIXTURES / f"volvo_{model.lower()}_cenik.pdf"


def _variant(variants, trim: str, engine_fragment: str):
    return next(v for v in variants if v.trim == trim and engine_fragment in v.variant_name)


@pytest.mark.parametrize(
    ("model", "count"),
    [
        ("EX30", 14),
        ("EX40", 13),
        ("EC40", 12),
        ("EX60", 6),
        ("EX90", 11),
        ("ES90", 7),
        ("XC40", 11),
        ("XC60", 22),
        ("XC90", 14),
        ("V60", 6),
    ],
)
def test_volvo_parser_reads_every_priced_cell(model: str, count: int) -> None:
    variants = VolvoParser().parse(_fixture(model))
    assert len(variants) == count
    assert all(v.model == model for v in variants)
    assert all(v.currency == "CZK" and v.price for v in variants)


def test_volvo_parser_reads_ex30_matrix_with_wrapped_labels_and_headers() -> None:
    variants = VolvoParser().parse(_fixture("EX30"))
    assert all(v.powertrain == "EV" for v in variants)
    assert {v.trim for v in variants} == {
        "ULTRA Black Edition",
        "ULTRA",
        "PLUS Black Edition",
        "PLUS",
        "CORE",
        "ESSENTIAL",
    }

    # "ULTRA" / "BLACK EDITION" is printed on two lines around the G5 row,
    # and "P5 LONG RANGE" / "electric" around the "Motor" header line.
    top = _variant(variants, "ULTRA Black Edition", "P5 LONG RANGE electric")
    assert top.price == 1_215_600.0
    assert top.source_page == 3
    assert "G5 - - 1 215 600 Kč 1 275 600 Kč" in top.raw_text

    # "-" cells are skipped: ESSENTIAL is only offered with P3/P5.
    essential = [v for v in variants if v.trim == "ESSENTIAL"]
    assert [v.price for v in essential] == [815_000.0, 865_000.0]
    assert _variant(variants, "ESSENTIAL", "P3 electric").variant_name == "EX30 ESSENTIAL P3 electric 110 kW"


def test_volvo_parser_reads_both_xc60_powertrain_tables() -> None:
    # Plug-in Hybrid matrix on page 3 (8 trims x T6/T8, CORE/ESSENTIAL
    # T6-only = 14) and Mild Hybrid on page 19 (8 trims x B5 = 8).
    variants = VolvoParser().parse(_fixture("XC60"))
    phev = [v for v in variants if v.powertrain == "PHEV"]
    mhev = [v for v in variants if v.powertrain == "MHEV"]
    assert len(phev) == 14
    assert {v.source_page for v in phev} == {3}
    assert len(mhev) == 8
    assert {v.source_page for v in mhev} == {19}

    # Bright/Dark theme descriptions in parentheses are dropped.
    assert _variant(variants, "PLUS Bright", "T8 AWD").price == 1_963_700.0
    assert _variant(variants, "ESSENTIAL", "B5 AWD").price == 1_517_900.0
    # Hybrid power is a per-motor breakdown - no single kW figure appended.
    assert "kW" not in _variant(variants, "CORE", "T6 AWD").variant_name


def test_volvo_parser_handles_code_row_without_kod_label_and_footnote_marks() -> None:
    # EC40's bottom row reads just "Varianta" (no "Kód"); EX90's labels
    # carry a "¹" footnote mark ("BLACK EDITION ¹").
    ec40 = VolvoParser().parse(_fixture("EC40"))
    assert _variant(ec40, "CORE", "P5 Long Range electric").price == 1_374_100.0

    ex90 = VolvoParser().parse(_fixture("EX90"))
    assert _variant(ex90, "PLUS Black Edition", "TWIN MOTOR Performance").price == 2_628_900.0
    assert _variant(ex90, "CORE", "SINGLE MOTOR").price == 2_138_900.0


def test_volvo_parser_reads_three_line_engine_headers() -> None:
    # ES90's headers wrap over up to three lines ("SINGLE MOTOR" /
    # "Extended Range", "TWIN MOTOR" / "Performance").
    variants = VolvoParser().parse(_fixture("ES90"))
    assert _variant(variants, "ULTRA", "SINGLE MOTOR Extended Range").price == 2_007_900.0
    assert _variant(variants, "PLUS", "TWIN MOTOR Performance").price == 2_109_900.0
    assert len([v for v in variants if v.trim == "CORE"]) == 1
