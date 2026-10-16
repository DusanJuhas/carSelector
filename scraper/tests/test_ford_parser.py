"""Tests for FordParser on four real price lists (downloaded 2026-09-07
from ford.cz's asset CDN, effective 30 June/1 July/1 September 2026 — see
scraper/tests/fixtures/ford_*.pdf). Prices are transcribed by hand from the
PDF (cross-checked against a rendered page image for Kuga's more complex
rows, not just extracted text — see parsers/ford.py's module docstring for
why naive text extraction can't be trusted at face value here), same
discipline as test_kia_parser.py.

Row counts per fixture (10/26/6/2) were cross-checked by hand against
`page.extract_words()` output (and, for Kuga, a rendered page image) for
every fixture, not just spot-checked."""

from pathlib import Path

from scraper.parsers.ford import FordParser

FIXTURES = Path(__file__).parent / "fixtures"
PUMA = FIXTURES / "ford_puma_cenik.pdf"
KUGA = FIXTURES / "ford_kuga_cenik.pdf"
MUSTANG = FIXTURES / "ford_mustang_cenik.pdf"
BRONCO = FIXTURES / "ford_bronco_cenik.pdf"


def _variant(variants, trim: str, engine_fragment: str):
    return next(v for v in variants if v.trim == trim and engine_fragment in v.variant_name)


def test_ford_parser_extracts_puma_variants() -> None:
    # Titanium is only offered with the base 125k/manual engine (3 of 4
    # trim columns; BlueCruise Edition dashed) + 125k/Powershift (all 4) +
    # 155k/Powershift (3 of 4; Titanium dashed) = 3 + 4 + 3 = 10 rows.
    variants = FordParser().parse(PUMA)
    assert len(variants) == 10
    assert all(v.model == "Puma" for v in variants)
    assert all(v.currency == "CZK" for v in variants)
    assert all(v.powertrain == "MHEV" for v in variants)  # every Puma engine here is 1.0 EcoBoost Hybrid (mHEV)
    assert all(v.source_page == 2 for v in variants)

    base = _variant(variants, "Titanium", "6st. manuální")
    assert base.price == 629_500.0  # základní cena, not the 439 500 Kč Zvýhodněná (discounted) price

    # two Powershift rows both reach BlueCruise Edition - disambiguate by power figure
    low_power = _variant(variants, "BlueCruise Edition", "125 k (92 kW) 7st. Powershift")
    assert low_power.price == 845_500.0
    high_power = _variant(variants, "BlueCruise Edition", "155 k (114 kW) 7st. Powershift")
    assert high_power.price == 875_500.0


def test_ford_parser_skips_dashed_cells() -> None:
    # BlueCruise Edition isn't offered with the base manual-transmission
    # engine (dash in that column) - must not appear as a variant for it.
    variants = FordParser().parse(PUMA)
    manual = [v for v in variants if "6st. manuální" in v.variant_name]
    assert {v.trim for v in manual} == {"Titanium", "ST-Line", "ST-Line X"}
    assert "BlueCruise Edition" not in {v.trim for v in manual}


def test_ford_parser_extracts_kuga_variants_across_six_trims() -> None:
    # 6 trim columns (Titanium/Top Edition/ST-Line/ST-Line X/Active X/
    # BlueCruise Edition); the two plain EcoBoost rows only reach 4 of them
    # (Top Edition and BlueCruise Edition dashed), the three
    # HEV/PHEV rows reach all 6 -> 4 + 4 + 6 + 6 + 6 = 26 rows.
    variants = FordParser().parse(KUGA)
    assert len(variants) == 26
    assert all(v.model == "Kuga" for v in variants)

    ice = _variant(variants, "Titanium", "6st. manuální")
    assert ice.powertrain == "ICE"
    assert ice.price == 725_000.0

    hev = _variant(variants, "BlueCruise Edition", "180 k (132 kW)")
    assert hev.powertrain == "HEV"
    assert hev.price == 1_092_000.0

    phev = _variant(variants, "Active X", "243 k (178 kW)")
    assert phev.powertrain == "PHEV"
    assert phev.price == 1_146_000.0

    awd = _variant(variants, "Titanium", "134 kW")
    assert "AWD" in awd.variant_name
    assert awd.price == 952_000.0


def test_ford_parser_extracts_mustang_variants_and_drops_trailing_note() -> None:
    # GT manual/automatic reach both trims (Fastback/Convertible); Dark
    # Horse manual/automatic are Fastback-only (Convertible dashed) ->
    # 2 + 2 + 1 + 1 = 6 rows. The "Dodatečné zvýhodnění ... skladové
    # vozy ..." bonus note printed directly below the last price row must
    # not leak into the last row's variant_name.
    variants = FordParser().parse(MUSTANG)
    assert len(variants) == 6
    assert all(v.model == "Mustang" for v in variants)

    dark_horse_auto = _variant(variants, "Fastback", "DARK HORSE benzín 453 k (334 kW) 10st. automatická")
    assert dark_horse_auto.price == 2_014_900.0
    assert "Dodatečné" not in dark_horse_auto.variant_name
    assert "Dodatečné" not in dark_horse_auto.raw_text

    manual = [v for v in variants if "DARK HORSE" in v.variant_name and "6st. manuální" in v.variant_name]
    assert {v.trim for v in manual} == {"Fastback"}


def test_ford_parser_extracts_bronco_variants() -> None:
    variants = FordParser().parse(BRONCO)
    assert len(variants) == 2
    assert {v.trim for v in variants} == {"Outer Banks", "Badlands"}
    assert all(v.model == "Bronco" for v in variants)
    assert all(v.powertrain == "ICE" for v in variants)

    badlands = _variant(variants, "Badlands", "335 k (246 kW)")
    assert badlands.price == 1_870_900.0


def test_ford_parser_raw_text_traceable_to_source() -> None:
    variants = FordParser().parse(PUMA)
    variant = _variant(variants, "Titanium", "6st. manuální")
    assert "629" in variant.raw_text
    assert "500" in variant.raw_text
    assert variant.source_page == 2


PUMA_2026_10 = FIXTURES / "ford_puma_cenik_2026_10.pdf"


def test_ford_parser_keeps_closely_spaced_trim_columns_apart() -> None:
    # The 1 October 2026 Puma list (5 trims, adds EDITION REPRE) prints
    # "ST-Line X" and "BlueCruise Edition" only 13.5pt apart - a 15pt header
    # gap threshold merged them into one column and glued their two prices
    # into one number (780 500 + 845 500 -> 780500845500). Rows: 4 (manual,
    # BlueCruise dashed) + 5 (125k Powershift) + 4 (155k, Titanium dashed).
    variants = FordParser().parse(PUMA_2026_10)
    assert len(variants) == 13
    assert {v.trim for v in variants} == {"Titanium", "ST-Line", "EDITION REPRE", "ST-Line X", "BlueCruise Edition"}
    assert all(v.price < 10_000_000 for v in variants)

    assert _variant(variants, "ST-Line X", "125 k (92 kW) 7st. Powershift").price == 780_500.0
    assert _variant(variants, "BlueCruise Edition", "125 k (92 kW) 7st. Powershift").price == 845_500.0
    assert _variant(variants, "ST-Line X", "155 k (114 kW) 7st. Powershift").price == 810_500.0
    assert _variant(variants, "BlueCruise Edition", "155 k (114 kW) 7st. Powershift").price == 875_500.0

    manual = [v for v in variants if "6st. manuální" in v.variant_name]
    assert "BlueCruise Edition" not in {v.trim for v in manual}
    assert _variant(variants, "ST-Line X", "6st. manuální").price == 725_500.0


def test_ford_parser_never_concatenates_two_prices_in_one_column() -> None:
    # Defensive guard: if a header column is ever missed again, a cell
    # holding two separate prices must be dropped, not glued together.
    from scraper.parsers.ford import _classify_row_words

    def word(text: str, x0: float) -> dict:
        return {"text": text, "x0": x0, "x1": x0 + 12.0, "top": 100.0}

    columns = [("ST-Line X", 485.5)]
    one_price = [word("780", 490.6), word("500", 503.9)]
    two_prices = one_price + [word("845", 541.2), word("500", 554.8)]

    assert _classify_row_words(one_price, columns)[1] == {"ST-Line X": "780500"}
    assert _classify_row_words(two_prices, columns)[1] == {}
