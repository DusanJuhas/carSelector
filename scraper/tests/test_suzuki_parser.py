"""Tests for SuzukiParser on all six real price lists (downloaded
2026-11-02 from auto.suzuki.cz, valid from 12 October 2026 - see
scraper/tests/fixtures/suzuki_*.pdf). Prices and row counts are
transcribed by hand from each document's "Motorizace" table text.

Like the other brands' reduced fixtures, these are the real documents
with photos replaced by a 1x1 pixel (text and layout unchanged); the
parser's output was checked to be identical on the original and the
reduced file for all six."""

from pathlib import Path

import pytest

from scraper.parsers.suzuki import SuzukiParser

FIXTURES = Path(__file__).parent / "fixtures"


def _parse(name: str):
    return SuzukiParser().parse(FIXTURES / f"suzuki_{name}_cenik.pdf")


@pytest.mark.parametrize(
    ("name", "model", "count"),
    [
        ("swift", "Swift", 7),
        ("vitara", "Vitara", 13),
        ("vitara_black_edition", "Vitara", 4),
        ("s_cross", "S-Cross", 13),
        ("s_cross_black_edition", "S-Cross", 4),
        ("e_vitara", "e Vitara", 5),
    ],
)
def test_suzuki_parser_infers_model_and_reads_every_row(name: str, model: str, count: int) -> None:
    variants = _parse(name)
    assert len(variants) == count
    assert all(v.model == model for v in variants)


def test_suzuki_parser_reads_standard_price_not_bonus_price() -> None:
    # "1.2 DualJet ELEGANCE 5MT 4×4 AllGrip 60 503 900 Kč 22 000 Kč 481 900 Kč"
    swift = _parse("swift")
    row = next(v for v in swift if v.trim == "ELEGANCE" and "4×4" in v.variant_name)
    assert row.price == 503_900.0
    assert row.variant_name == "Swift ELEGANCE 1.2 DualJet 60 kW 5MT 4×4 AllGrip"
    assert all(v.powertrain == "MHEV" for v in swift)


def test_suzuki_parser_keeps_black_edition_and_panorama_in_trim() -> None:
    variants = _parse("vitara_black_edition")
    top = variants[-1]
    assert top.trim == "ELEGANCE PANORAMA Black Edition"  # footnote "*" dropped
    assert top.price == 704_900.0


def test_suzuki_parser_reads_e_vitara_battery_rows() -> None:
    variants = _parse("e_vitara")
    assert all(v.powertrain == "EV" for v in variants)
    top = next(v for v in variants if v.trim == "ELEGANCE" and "4×4" in v.variant_name)
    assert top.variant_name == "e Vitara ELEGANCE 61 kWh 135 kW 4×4"
    assert top.price == 1_027_500.0
