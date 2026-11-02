"""Tests for HondaParser on all six real price lists (downloaded
2026-11-02 from honda.cz, model year 2027, valid from 10 October 2026 -
see scraper/tests/fixtures/honda_*.pdf). Prices are transcribed by hand
from each document's page-1 price table text.

The fixtures are the real 2-page documents with images replaced by a 1x1
pixel; the parser's output was checked to be identical on the original
and the reduced file for all six."""

from datetime import date
from pathlib import Path

import pdfplumber
import pytest

from scraper.parsers._pdf_layout import extract_release_date
from scraper.parsers.honda import HondaParser

FIXTURES = Path(__file__).parent / "fixtures"


def _fixture(name: str) -> Path:
    return FIXTURES / f"honda_{name}_cenik.pdf"


@pytest.mark.parametrize(
    ("name", "model", "count"),
    [
        ("jazz", "Jazz", 4),
        ("civic", "Civic", 3),
        ("hr_v", "HR-V", 5),
        ("zr_v", "ZR-V", 3),
        ("cr_v", "CR-V", 5),
        ("prelude", "Prelude", 2),
    ],
)
def test_honda_parser_reads_every_row(name: str, model: str, count: int) -> None:
    variants = HondaParser().parse(_fixture(name))
    assert len(variants) == count
    assert all(v.model == model for v in variants)


def test_honda_parser_does_not_merge_co2_into_price() -> None:
    # "Elegance 1.5 i-MMD Hybrid 96/131 Automatická 5,4 122 744 900":
    # CO2 122 g/km, then 744 900 Kč - never 122 744 900.
    variants = HondaParser().parse(_fixture("hr_v"))
    assert [v.price for v in variants] == [744_900.0, 804_900.0, 824_900.0, 889_900.0, 914_900.0]


def test_honda_parser_reads_seven_figure_price_after_co2() -> None:
    # "Elegance AWD 2.0 i-MMD Hybrid 135/184 Automatická 6,7 – 151 1 174 900"
    variants = HondaParser().parse(_fixture("cr_v"))
    awd = next(v for v in variants if v.trim == "Elegance" and "AWD" in v.variant_name)
    assert awd.price == 1_174_900.0
    assert awd.variant_name == "CR-V Elegance 2.0 i-MMD Hybrid 135 kW AWD"


def test_honda_parser_classifies_cr_v_plug_in_section() -> None:
    variants = HondaParser().parse(_fixture("cr_v"))
    assert [v.powertrain for v in variants] == ["HEV", "HEV", "HEV", "PHEV", "PHEV"]
    assert variants[-1].trim == "Advance Tech"
    assert variants[-1].price == 1_374_900.0


def test_honda_cover_date_is_read_as_release_date() -> None:
    with pdfplumber.open(_fixture("civic")) as pdf:
        assert extract_release_date(pdf) == date(2026, 10, 10)
