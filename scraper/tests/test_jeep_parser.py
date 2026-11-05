"""Tests for JeepParser on all ten real price lists (downloaded 2026-11-05
from jeep.cz - see scraper/tests/fixtures/jeep_*.pdf). Prices and row
counts are transcribed by hand from each document's "CENÍKOVÉ A AKČNÍ
CENY" page.

The fixtures keep only that price page, with photos replaced by a 1x1
pixel; the parser's output was checked to be identical on the original
and the reduced file for all ten."""

from pathlib import Path

import pytest

from scraper.monitors.discovery.jeep import JeepDiscoverer
from scraper.parsers.jeep import JeepParser

FIXTURES = Path(__file__).parent / "fixtures"


def _parse(name: str):
    return JeepParser().parse(FIXTURES / f"jeep_{name}_cenik.pdf")


@pytest.mark.parametrize(
    ("name", "model", "powertrains", "count"),
    [
        ("avenger", "Avenger", {"ICE", "MHEV"}, 8),
        ("avenger_4xe", "Avenger", {"MHEV"}, 3),
        ("avenger_electric", "Avenger", {"EV"}, 4),
        ("compass_e_hybrid", "Compass", {"MHEV"}, 3),
        ("compass_e_hybrid_plug_in", "Compass", {"PHEV"}, 2),
        ("compass_electric", "Compass", {"EV"}, 5),
        ("compass_4xe_electric", "Compass", {"EV"}, 2),
        ("grand_cherokee", "Grand Cherokee", {"PHEV"}, 2),
        ("wrangler", "Wrangler", {"ICE"}, 2),
        ("wrangler_4xe", "Wrangler", {"PHEV"}, 2),
    ],
)
def test_jeep_parser_reads_every_row(name: str, model: str, powertrains: set[str], count: int) -> None:
    variants = _parse(name)
    assert len(variants) == count
    assert {v.model for v in variants} == {model}
    assert {v.powertrain for v in variants} == powertrains


def test_jeep_parser_reads_list_price_and_recases_trim_headings() -> None:
    # "85TH ANNIVERSARY / 619.82K.4 1.2 Turbo e-Hybrid 110k 81kW/110k Benzín
    # 6st. automatická Přední 749 900 Kč 639 900 Kč"
    variants = _parse("avenger")
    row = next(v for v in variants if v.trim == "85th Anniversary" and v.powertrain == "MHEV")
    assert row.price == 749_900.0
    assert row.variant_name == "Avenger 85th Anniversary 1.2 Turbo e-Hybrid 110k 81 kW Benzín 6st. automatická Přední"
    assert [v.trim for v in variants] == ["Longitude"] * 2 + ["Altitude"] * 2 + ["85th Anniversary"] * 2 + [
        "Summit"
    ] * 2


def test_jeep_parser_keeps_drive_and_mixed_case_trims() -> None:
    variants = _parse("grand_cherokee")
    assert [(v.trim, v.price) for v in variants] == [("Limited", 2_349_900.0), ("Summit Reserve", 2_699_900.0)]
    assert all(v.variant_name.endswith("4WD") for v in variants)


def test_jeep_parser_skips_stock_footnote_between_rows() -> None:
    # Compass Electric's "First Edition" row carries a "*" and a
    # "* Pouze skladové zásoby" footnote follows the table.
    variants = _parse("compass_electric")
    assert [(v.trim, v.price) for v in variants] == [
        ("Altitude", 1_129_900.0),
        ("Altitude", 1_229_900.0),
        ("First Edition", 1_199_900.0),
        ("Summit", 1_209_900.0),
        ("Summit", 1_309_900.0),
    ]


@pytest.mark.parametrize(
    ("filename", "key"),
    [
        ("Novy_Jeep_Avenger_4xe_01-11-2026", "Avenger 4xe"),
        ("Jeep_Compass_e-Hybrid_Plug-in_01-11-2026", "Compass e-Hybrid Plug-in"),
        ("Jeep_GrandCherokee_01-09-2026", "Grand Cherokee"),
        ("Jeep_WranglerICE_01-09-2026", "Wrangler"),
        ("Jeep_WranglerPHEV_01-09-2026", "Wrangler 4xe"),
    ],
)
def test_jeep_discoverer_document_key(filename: str, key: str) -> None:
    assert JeepDiscoverer().document_key(filename) == key
