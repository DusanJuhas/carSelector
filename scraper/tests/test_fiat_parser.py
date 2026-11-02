"""Tests for FiatParser on all nine real price lists (downloaded
2026-11-02 from fiatcz.com, valid 1-31 October 2026 - see
scraper/tests/fixtures/fiat_*.pdf). Prices and row counts are
transcribed by hand from each document's "CENÍKOVÉ (A AKČNÍ) CENY" page.

The fixtures keep the first pages (the price page among them) with
photos replaced by a 1x1 pixel; the parser's output was checked to be
identical on the original and the reduced file for all nine."""

from pathlib import Path

import pytest

from scraper.parsers.fiat import FiatParser

FIXTURES = Path(__file__).parent / "fixtures"


def _parse(name: str):
    return FiatParser().parse(FIXTURES / f"fiat_{name}_cenik.pdf")


@pytest.mark.parametrize(
    ("name", "models", "count"),
    [
        ("500_hybrid", {"500"}, 11),
        ("500e", {"500"}, 10),
        ("600", {"600"}, 13),
        ("600e", {"600"}, 4),
        ("grande_panda", {"Grande Panda"}, 6),
        ("grande_panda_electric", {"Grande Panda"}, 3),
        ("pandina", {"Pandina"}, 3),
        ("tipo_sedan", {"Tipo Sedan"}, 2),
        ("qubo_l", {"Qubo L", "Qubo L Maxi"}, 18),
    ],
)
def test_fiat_parser_reads_every_row(name: str, models: set[str], count: int) -> None:
    variants = _parse(name)
    assert len(variants) == count
    assert {v.model for v in variants} == models


def test_fiat_parser_reads_list_price_and_trim_headings() -> None:
    # "Icon / 364.J23.3 1.2 Turbo Hybrid 110k 81kW/110k Benzín 6st. automatická 649 900 Kč 574 900 Kč"
    variants = _parse("600")
    row = next(v for v in variants if v.trim == "Icon" and "Hybrid 110k" in v.variant_name)
    assert row.price == 649_900.0
    assert row.powertrain == "MHEV"
    assert row.variant_name == "600 Icon 1.2 Turbo Hybrid 110k 81 kW Benzín 6st. automatická"
    assert {v.trim for v in variants} == {"Pop", "Icon", "Street", "La Prima", "Sport"}


def test_fiat_parser_files_electric_twin_under_nameplate() -> None:
    variants = _parse("600e")
    assert all(v.model == "600" and v.powertrain == "EV" for v in variants)
    assert variants[0].price == 799_900.0


def test_fiat_parser_keeps_500_body_style_in_variant_name() -> None:
    variants = _parse("500e")
    cabrio = next(v for v in variants if v.trim == "La Prima" and "Cabrio" in v.variant_name)
    assert cabrio.price == 1_039_900.0


def test_fiat_parser_splits_qubo_l_maxi_and_keeps_diesel_marker() -> None:
    variants = _parse("qubo_l")
    maxi = next(
        v for v in variants if v.model == "Qubo L Maxi" and v.trim == "Prima Rodina" and "8st." in v.variant_name
    )
    assert maxi.price == 859_900.0
    assert "Diesel" in maxi.variant_name
    assert maxi.powertrain == "ICE"
