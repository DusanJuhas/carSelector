"""Tests for LexusParser on all ten real price lists (downloaded
2026-11-02 from content.lexus-ce.com - see scraper/tests/fixtures/
lexus_*.pdf). Prices and cell counts are transcribed by hand from each
document's page-2 price matrix ("—"/"–"/"-" cells counted out).

The originals are 3-12 MB of photography; the fixtures keep the first ten
pages (cover, price matrix and, for LBX, the colour page that names the
model) with images replaced by a 1x1 pixel. The parser's output was
checked to be identical on the original and the reduced file for all ten."""

from pathlib import Path

import pytest

from scraper.parsers.lexus import LexusParser

FIXTURES = Path(__file__).parent / "fixtures"


def _parse(name: str):
    return LexusParser().parse(FIXTURES / f"lexus_{name}_cenik.pdf")


def _cell(variants, trim: str, engine_fragment: str):
    return next(v for v in variants if v.trim == trim and v.variant_name.endswith(engine_fragment))


@pytest.mark.parametrize(
    ("name", "model", "count"),
    [
        ("lbx", "LBX", 11),
        ("ux", "UX", 7),
        ("nx350", "NX", 11),
        ("nx450", "NX", 6),
        ("es", "ES", 8),
        ("rx350h", "RX", 5),
        ("rx450h", "RX", 5),
        ("rx500h", "RX", 1),
        ("rz", "RZ", 9),
        ("lm", "LM", 4),
    ],
)
def test_lexus_parser_reads_every_priced_cell(name: str, model: str, count: int) -> None:
    variants = _parse(name)
    assert len(variants) == count
    assert all(v.model == model and v.source_page == 2 for v in variants)


def test_lexus_parser_maps_cells_to_columns_with_interleaved_sfx_codes() -> None:
    # "PRESTIGE TOP 1 790 000 KČ GA 1 870 000 KČ JA — — — —" - two cells,
    # each followed by its own SFX code, then two unavailable engines.
    variants = _parse("es")
    assert _cell(variants, "PRESTIGE TOP", "300h AWD").price == 1_870_000.0
    assert {v.variant_name for v in variants if v.trim == "PRESTIGE TOP"} == {
        "ES PRESTIGE TOP 300h FWD",
        "ES PRESTIGE TOP 300h AWD",
    }
    luxury = _cell(variants, "LUXURY", "350e FWD")
    assert luxury.price == 2_160_000.0
    assert luxury.powertrain == "EV"
    assert _cell(variants, "PRESTIGE", "300h FWD").powertrain == "HEV"


def test_lexus_parser_ignores_all_digit_sfx_codes() -> None:
    # "ELEGANCE 1 920 000 KČ 15" - "15" is an order code, not a price digit.
    variants = _parse("rx350h")
    assert [v.price for v in variants] == [1_920_000.0, 1_970_000.0, 2_200_000.0, 2_230_000.0, 2_490_000.0]


def test_lexus_parser_reads_plug_in_and_awd_columns() -> None:
    nx450 = _parse("nx450")
    assert all(v.powertrain == "PHEV" for v in nx450)
    nx350 = _parse("nx350")
    assert _cell(nx350, "EXECUTIVE TOP", "350h 4X4 E-FOUR").price == 1_780_000.0
    assert not [v for v in nx350 if v.trim == "EXECUTIVE TOP" and v.variant_name.endswith("FWD")]


def test_lexus_parser_reads_lm_seat_columns_and_lbx_without_cover_text() -> None:
    lm = _parse("lm")
    assert _cell(lm, "LUXURY VIP", "350h 4 MÍSTA").price == 3_990_000.0
    lbx = _parse("lbx")
    assert _cell(lbx, "COOL", "4X4 E-FOUR").price == 1_140_000.0
    assert all(v.powertrain == "HEV" for v in lbx)
