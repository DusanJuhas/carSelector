"""Tests for NissanParser on the five real passenger-car price lists
nissan.cz's homepage links (downloaded 2026-11-02 - see
scraper/tests/fixtures/nissan_*.pdf). Prices and row counts are
transcribed by hand from each price table, read against word
coordinates where the extracted text interleaves wrapped cells.

The fixtures keep the first four pages (cover and price table) with
images replaced by a 1x1 pixel; the parser's output was checked to be
identical on the original and the reduced file for all five."""

from pathlib import Path

from scraper.parsers.nissan import NissanParser

FIXTURES = Path(__file__).parent / "fixtures"


def _parse(name: str):
    return NissanParser().parse(FIXTURES / f"nissan_{name}_cenik.pdf")


def test_nissan_parser_reads_qashqai_inconsistent_price_formats() -> None:
    # "784 990Kč", "829990Kč", "1 004 990Kč" - all list prices.
    variants = _parse("qashqai")
    assert len(variants) == 14
    assert [v.price for v in variants[:3]] == [784_990.0, 829_990.0, 939_990.0]
    assert variants[11].price == 1_004_990.0
    assert {v.trim for v in variants} == {"ACENTA", "N-CONNECTA", "TEKNA", "TEKNA PLUS"}


def test_nissan_parser_keeps_wrapped_engine_line_out_of_trim() -> None:
    # The first row's engine wraps onto "+ ColdPackv ceně", which sits
    # nearer the trim column's header than the engine column's.
    first = _parse("qashqai")[0]
    assert first.trim == "ACENTA"
    assert first.variant_name == "Qashqai ACENTA 1.3 DIG-T mHEV 2WD, 6MT + ColdPackv ceně 116 kW"
    assert first.powertrain == "MHEV"


def test_nissan_parser_reads_juke_and_ignores_off_page_summary_table() -> None:
    variants = _parse("juke")
    assert len(variants) == 11
    tekna = [v for v in variants if v.trim == "TEKNA"]
    assert [v.price for v in tekna] == [718_600.0, 761_600.0, 813_700.0]
    # One wrapped label for a two-row group.
    assert [v.price for v in variants if v.trim == "N-DESIGN, N-SPORT"] == [799_900.0, 852_000.0]
    assert next(v for v in variants if "1.6 HEV" in v.variant_name).powertrain == "HEV"


def test_nissan_parser_reads_x_trail_and_its_summer_edition() -> None:
    regular = _parse("x_trail")
    assert len(regular) == 10
    assert all(v.powertrain == "HEV" for v in regular)  # e-POWER
    assert regular[-1].variant_name == "X-Trail TEKNA PLUS e-POWER e-4ORCE, 4WD 157 kW"
    assert regular[-1].price == 1_399_990.0

    summer = _parse("x_trail_summer_edition")
    assert [(v.trim, v.price) for v in summer] == [
        ("ACENTA Summer Edition", 989_990.0),
        ("ACENTA Summer Edition", 1_119_990.0),
        ("N-CONNECTA Summer Edition", 1_179_990.0),
    ]


def test_nissan_parser_reads_micra_transposed_table() -> None:
    variants = _parse("micra")
    assert [(v.trim, v.variant_name, v.price) for v in variants] == [
        ("ENGAGE", "Micra ENGAGE 40 kWh –120k", 659_000.0),
        ("ADVANCE", "Micra ADVANCE 40 kWh –120k", 744_000.0),
        ("ADVANCE", "Micra ADVANCE 52 kWh –150k", 800_000.0),
        ("EVOLVE", "Micra EVOLVE 52 kWh –150k", 849_000.0),
    ]
    assert all(v.powertrain == "EV" for v in variants)
