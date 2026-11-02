"""Tests for MitsubishiParser on ten real price lists (downloaded
2026-11-02 from mitsubishi-motors.cz, valid 1-30 November 2026 - see
scraper/tests/fixtures/mitsubishi_*.pdf). Prices and row counts are
transcribed by hand from each document's own page-3 "CENÍK ..." table
text, same discipline as test_mg_parser.py.

The fixtures are the real documents with every page except the cover
and the price page blanked and photos removed (the originals are ~2-3
MB) - page numbers, text and the table's own cell borders (which the
parser uses) are unchanged, and the parser's output was checked to be
identical on the original and the reduced file for all ten."""

from pathlib import Path

from scraper.parsers.mitsubishi import MitsubishiParser

FIXTURES = Path(__file__).parent / "fixtures"
COLT = FIXTURES / "mitsubishi_colt_cenik.pdf"
COLT_HYBRID = FIXTURES / "mitsubishi_colt_hybrid_cenik.pdf"
ASX = FIXTURES / "mitsubishi_asx_cenik.pdf"
ASX_LIMITED = FIXTURES / "mitsubishi_asx_limited_cenik.pdf"
GRANDIS = FIXTURES / "mitsubishi_grandis_cenik.pdf"
ECLIPSE_CROSS = FIXTURES / "mitsubishi_eclipse_cross_bev_cenik.pdf"
OUTLANDER = FIXTURES / "mitsubishi_outlander_phev_cenik.pdf"
OUTLANDER_BLACK = FIXTURES / "mitsubishi_outlander_phev_black_edition_cenik.pdf"
OUTLANDER_DIAMOND = FIXTURES / "mitsubishi_outlander_phev_diamond_cenik.pdf"
OUTLANDER_25 = FIXTURES / "mitsubishi_outlander_phev_25let_cenik.pdf"


def _variant(variants, trim: str, engine_fragment: str):
    return next(v for v in variants if v.trim == trim and engine_fragment in v.variant_name)


def test_mitsubishi_parser_assigns_merged_trim_cells_by_drawn_borders() -> None:
    # INFORM (1 row), INVITE+ (2), INTENSE+ (3), INSTYLE (1). INTENSE+'s
    # last row is as close to the INSTYLE label as to its own - only the
    # table's own cell borders tell them apart.
    variants = MitsubishiParser().parse(ASX)
    assert len(variants) == 7
    assert all(v.model == "ASX" for v in variants)
    assert [v.trim for v in variants] == ["INFORM", "INVITE+", "INVITE+", "INTENSE+", "INTENSE+", "INTENSE+", "INSTYLE"]

    hev = _variant(variants, "INTENSE+", "1.8 HYBRID (HEV)")
    assert hev.price == 746_790.0  # "Cena", not the "Akční cena" 699 790
    assert hev.powertrain == "HEV"
    assert hev.source_page == 3
    assert _variant(variants, "INSTYLE", "1.3 DI-T MILD HYBRID").powertrain == "MHEV"
    assert _variant(variants, "INFORM", "1.2 DI-T").powertrain == "ICE"
    assert _variant(variants, "INFORM", "1.2 DI-T").variant_name == "ASX INFORM 1.2 DI-T 84 kW 6MT 2WD"


def test_mitsubishi_parser_extracts_colt_petrol_and_hybrid_documents() -> None:
    colt = MitsubishiParser().parse(COLT)
    assert len(colt) == 5
    assert all(v.model == "Colt" and v.powertrain == "ICE" for v in colt)
    assert _variant(colt, "INVITE", "1.0 MPI 49 kW").price == 418_960.0
    assert _variant(colt, "INSTYLE", "1.0 MPI-T").price == 528_960.0

    hybrid = MitsubishiParser().parse(COLT_HYBRID)
    assert len(hybrid) == 3
    assert all(v.model == "Colt" and v.powertrain == "HEV" for v in hybrid)
    assert _variant(hybrid, "INTENSE+", "1.6 HYBRID").price == 604_960.0


def test_mitsubishi_parser_extracts_grandis() -> None:
    variants = MitsubishiParser().parse(GRANDIS)
    assert len(variants) == 8
    assert all(v.model == "Grandis" for v in variants)
    assert _variant(variants, "INVITE+", "7DCT").price == 714_760.0
    assert _variant(variants, "INSTYLE+", "1.8 HYBRID").price == 899_760.0


def test_mitsubishi_parser_extracts_eclipse_cross_without_motor_column() -> None:
    variants = MitsubishiParser().parse(ECLIPSE_CROSS)
    assert len(variants) == 2
    assert all(v.model == "Eclipse Cross" and v.powertrain == "EV" for v in variants)
    instyle = _variant(variants, "INSTYLE", "87 kWh")
    assert instyle.price == 1_233_850.0
    assert instyle.variant_name == "Eclipse Cross INSTYLE 87 kWh 160 kW S fixním převodem 2WD"


def test_mitsubishi_parser_extracts_outlander_phev_and_skips_package_rows() -> None:
    # The "PAKET TRAIL 69 990 Kč" / "PAKET ELEGANCE ..." rows under the
    # table are optional packages, not variants.
    variants = MitsubishiParser().parse(OUTLANDER)
    assert len(variants) == 4
    assert all(v.model == "Outlander PHEV" and v.powertrain == "PHEV" for v in variants)
    assert all("4WD" in v.variant_name for v in variants)
    assert _variant(variants, "INSTYLE", "2.4 DOHC MIVEC").price == 1_575_950.0


def test_mitsubishi_parser_keeps_special_editions_as_trims() -> None:
    limited = MitsubishiParser().parse(ASX_LIMITED)
    assert [(v.model, v.trim, v.price) for v in limited] == [
        ("ASX", "LIMITED", 619_950.0),
        ("ASX", "LIMITED", 688_950.0),
    ]
    for path, trim, price in [
        (OUTLANDER_BLACK, "BLACK EDITION", 1_656_450.0),
        (OUTLANDER_DIAMOND, "DIAMOND TOP", 1_575_950.0),
        (OUTLANDER_25, "25 LET OUTLANDER", 1_461_950.0),
    ]:
        variants = MitsubishiParser().parse(path)
        assert [(v.model, v.trim, v.price) for v in variants] == [("Outlander PHEV", trim, price)]
