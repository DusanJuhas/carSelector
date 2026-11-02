"""Tests for SubaruParser on all five real price lists (downloaded
2026-11-02 from subaru.cz - see scraper/tests/fixtures/subaru_*.pdf).
Prices are transcribed by hand from each document's price table, read
against word coordinates where the extracted text runs prices together
(Forester's "847 107 1 025 000 985 000").

The fixtures keep the first three pages with images replaced by a 1x1
pixel; the parser's output was checked to be identical on the original
and the reduced file for all five."""

from pathlib import Path

from scraper.parsers.subaru import SubaruParser

FIXTURES = Path(__file__).parent / "fixtures"


def _parse(name: str):
    return SubaruParser().parse(FIXTURES / f"subaru_{name}_cenik.pdf")


def test_subaru_parser_reads_forester_incl_vat_column() -> None:
    # Columns: ex-VAT 847 107 | incl. VAT 1 025 000 | promo 985 000.
    variants = _parse("forester")
    assert [(v.trim, v.price) for v in variants] == [
        ("ACTIVE", 1_025_000.0),
        ("COMFORT", 1_100_000.0),
        ("FIELD", 1_190_000.0),
        ("TOURING", 1_255_000.0),
    ]
    assert variants[0].variant_name == "Forester ACTIVE FB20 100 kW (136 k) CVT"
    assert all(v.powertrain == "MHEV" for v in variants)


def test_subaru_parser_reads_impreza_wrapped_engine_cell() -> None:
    variants = _parse("impreza")
    assert [(v.trim, v.price) for v in variants] == [("ACTIVE", 845_000.0), ("EXECUTIVE", 950_000.0)]
    assert "e-Boxer FB20 100 kW (136 k)" in variants[0].variant_name


def test_subaru_parser_maps_uncharted_prices_to_trim_columns() -> None:
    # "-" cells are skipped: 58 FWD only LIMITED, 77 FWD only COMFORT,
    # 77 AWD only EXECUTIVE/TOURING; promotional "Kč*" prices ignored.
    variants = _parse("uncharted")
    assert [(v.trim, v.variant_name, v.price) for v in variants] == [
        ("LIMITED", "Uncharted LIMITED 58 FWD", 920_000.0),
        ("COMFORT", "Uncharted COMFORT 77 FWD", 1_060_000.0),
        ("EXECUTIVE", "Uncharted EXECUTIVE 77 AWD", 1_190_000.0),
        ("TOURING", "Uncharted TOURING 77 AWD", 1_220_000.0),
    ]
    assert all(v.powertrain == "EV" for v in variants)


def test_subaru_parser_reads_spec_label_on_its_own_line_and_skips_surcharges() -> None:
    # Solterra/e-Outback print "AWD 73" / "75 AWD" a line above the prices,
    # and a "20 000 Kč / 23 000 Kč" paint surcharge below the table.
    solterra = _parse("solterra")
    assert [v.price for v in solterra] == [1_160_000.0, 1_220_000.0, 1_270_000.0, 1_320_000.0]
    e_outback = _parse("e_outback")
    assert e_outback[0].model == "e-Outback"
    assert e_outback[0].variant_name == "e-Outback LIMITED 75 AWD 280 kW"
    assert len(e_outback) == 4
