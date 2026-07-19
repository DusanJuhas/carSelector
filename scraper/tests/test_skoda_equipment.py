"""Test for parse_standalone_equipment on a real Octavia price list (same
fixture as test_parsers.py). Availability/prices are transcribed by hand
from the `extract_text()` output of p. 18 ("Samostatné prvky výbavy"),
not derived from the parser — same discipline as the other tests.

Legend in the PDF: "●" = available (always OPTIONAL, items have a price,
they aren't free), "–" = not available for that trim (no record)."""
from pathlib import Path

import pdfplumber

from scraper.parsers.skoda_equipment import parse_standalone_equipment
from scraper.parsers.skoda_ice import SkodaIceParser

FIXTURE = Path(__file__).parent / "fixtures" / "skoda_octavia_cenik.pdf"


def _parse():
    with pdfplumber.open(FIXTURE) as pdf:
        return parse_standalone_equipment(pdf)


def test_finds_all_eight_trims_in_correct_order() -> None:
    data = _parse()
    assert list(data.keys()) == [
        "Essence",
        "Selection",
        "Classic",
        "Top Selection",
        "Dynamic",
        "Exclusive Selection",
        "Sportline",
        "RS",
    ]


def test_item_available_for_all_trims() -> None:
    # "Příprava pro tažné zařízení ● ● ● ● ● ● ● ● 5 000" — available everywhere
    data = _parse()
    for trim, items in data.items():
        assert items.get("Příprava pro tažné zařízení") == "OPTIONAL", trim


def test_item_available_only_for_essence() -> None:
    # "Rezervní kolo - plnohodnotné ● – – – – – – – 3 900"
    data = _parse()
    assert data["Essence"]["Rezervní kolo - plnohodnotné"] == "OPTIONAL"
    for trim in ("Selection", "Classic", "Top Selection", "Dynamic", "Exclusive Selection", "Sportline", "RS"):
        assert "Rezervní kolo - plnohodnotné" not in data[trim]


def test_item_unavailable_for_essence_only() -> None:
    # "Rezervní kolo - dojezdové – ● ● ● ● ● ● ●"
    data = _parse()
    assert "Rezervní kolo - dojezdové" not in data["Essence"]
    for trim in ("Selection", "Classic", "Top Selection", "Dynamic", "Exclusive Selection", "Sportline", "RS"):
        assert data[trim]["Rezervní kolo - dojezdové"] == "OPTIONAL"


def test_wrapped_multiline_item_name_is_skipped_not_guessed() -> None:
    # "Elektrická přední sedadla s pamětí a zrcátka s osvětlením
    #  nástupního prostoru" — name wrapped across 2 lines outside the data
    # row with the symbols, better to skip it than invent a wrong name.
    data = _parse()
    all_items = {name for items in data.values() for name in items}
    assert not any("Elektrická přední sedadla" in name for name in all_items)


def test_essence_has_expected_item_count() -> None:
    data = _parse()
    assert len(data["Essence"]) == 8


def test_skoda_ice_parser_attaches_equipment_to_variants_by_trim() -> None:
    variants = SkodaIceParser().parse(FIXTURE)

    essence_variant = next(v for v in variants if v.trim == "Essence")
    assert essence_variant.equipment.get("Rezervní kolo - plnohodnotné") == "OPTIONAL"
    assert "Rezervní kolo - dojezdové" not in essence_variant.equipment

    selection_variant = next(v for v in variants if v.trim == "Selection")
    assert "Rezervní kolo - plnohodnotné" not in selection_variant.equipment
    assert selection_variant.equipment.get("Rezervní kolo - dojezdové") == "OPTIONAL"
