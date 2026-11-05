"""Tests for AlfaRomeoParser on seven real price lists (downloaded
2026-11-05 from alfaromeocz.com, valid 1-30 November 2026 - see
scraper/tests/fixtures/alfa_romeo_*.pdf). Prices and row counts are
transcribed by hand from each document's "CENÍKOVÉ CENY" page.

The fixtures keep only that price page, with photos replaced by a 1x1
pixel; the parser's output was checked to be identical on the original
and the reduced file for all seven."""

from pathlib import Path

import pytest

from scraper.monitors.discovery.alfa_romeo import AlfaRomeoDiscoverer
from scraper.parsers.alfa_romeo import AlfaRomeoParser

FIXTURES = Path(__file__).parent / "fixtures"


def _parse(name: str):
    return AlfaRomeoParser().parse(FIXTURES / f"alfa_romeo_{name}_cenik.pdf")


@pytest.mark.parametrize(
    ("name", "model", "powertrains", "count"),
    [
        ("giulia", "Giulia", {"ICE"}, 5),
        ("giulia_quadrifoglio", "Giulia", {"ICE"}, 1),
        ("stelvio", "Stelvio", {"ICE"}, 4),
        ("stelvio_quadrifoglio", "Stelvio", {"ICE"}, 1),
        ("junior_ibrida", "Junior", {"MHEV"}, 4),
        ("junior_elettrica", "Junior", {"EV"}, 3),
        ("tonale_phev", "Tonale", {"PHEV"}, 4),
    ],
)
def test_alfa_romeo_parser_reads_every_row(name: str, model: str, powertrains: set[str], count: int) -> None:
    variants = _parse(name)
    assert len(variants) == count
    assert {v.model for v in variants} == {model}
    assert {v.powertrain for v in variants} == powertrains


def test_alfa_romeo_parser_keeps_diesel_and_drive_in_name() -> None:
    # "VELOCE / 620.1AC.7_V 2.2 JTDm Q4 154kW/210k Diesel 8st. automatická Q4 (AWD) 1 449 000 Kč"
    variants = _parse("giulia")
    row = next(v for v in variants if v.trim == "Veloce" and "Q4" in v.variant_name)
    assert row.price == 1_449_000.0
    assert row.variant_name == "Giulia Veloce 2.2 JTDm Q4 154 kW Diesel 8st. automatická Q4 (AWD)"
    assert {v.trim for v in variants} == {"Sprint", "Veloce", "Luna Rossa"}


def test_alfa_romeo_parser_files_quadrifoglio_as_trim() -> None:
    (row,) = _parse("stelvio_quadrifoglio")
    assert (row.model, row.trim, row.price) == ("Stelvio", "Quadrifoglio", 2_499_000.0)


def test_alfa_romeo_parser_does_not_repeat_trim_in_name() -> None:
    variants = _parse("junior_elettrica")
    assert [v.variant_name.split(" Elettrica")[0] for v in variants] == [
        "Junior",
        "Junior Sport Speciale",
        "Junior Veloce 280",
    ]
    assert [v.price for v in variants] == [979_000.0, 1_069_000.0, 1_219_000.0]


def test_alfa_romeo_parser_reads_tonale_phev() -> None:
    variants = _parse("tonale_phev")
    assert [(v.trim, v.price) for v in variants] == [
        ("Tonale", 1_219_000.0),
        ("Sprint", 1_249_000.0),
        ("Veloce", 1_349_000.0),
        ("Sport Speciale", 1_349_000.0),
    ]


@pytest.mark.parametrize(
    ("filename", "key"),
    [
        ("AR_Giulia_QV_01_11_2026", "Giulia Quadrifoglio"),
        ("AR_Junior_Elettrica_01_11_2026", "Junior Elettrica"),
        ("AR_Tonale_PHEV_01_11_2026", "Tonale PHEV"),
        ("AlfaRomeo_Stelvio_01-02-2026", "Stelvio"),
    ],
)
def test_alfa_romeo_discoverer_document_key(filename: str, key: str) -> None:
    assert AlfaRomeoDiscoverer().document_key(filename) == key
