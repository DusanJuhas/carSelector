"""Tests for KgmParser on all eight real price lists (downloaded
2026-11-05 from kgmcars.cz's widget CDN - see
scraper/tests/fixtures/kgm_*.pdf), and for KgmDiscoverer's offline
helpers. Prices are transcribed by hand from each document's rendered
price table (the struck-through list price, not the promotional one).

The fixtures keep only the price page (page 2), with photos replaced by a
1x1 pixel; the parser's output was checked to be identical on the
original and the reduced file for all eight."""

from pathlib import Path

import pytest

from scraper.monitors.discovery.kgm import price_list_urls, widget_config
from scraper.parsers.kgm import KgmParser

FIXTURES = Path(__file__).parent / "fixtures"
# The real file names the documents were downloaded under - Torres and
# Actyon print their model name nowhere else.
_URLS = {
    "torres": "https://cmsimages.carusseldwt.com/cms/downloads/PROD/CZ/Ssangyong/KGMCZ0000/b957a66b/202610_KGM_cenik-torres-facelift-CZ_30-11.pdf",
    "actyon": "https://cmsimages.carusseldwt.com/cms/downloads/PROD/CZ/Ssangyong/KGMCZ0000/97506fa8/202611_KGM_cenik_Actyon_CZ.pdf",
}


def _parse(name: str, *, with_url: bool = True):
    parser = KgmParser()
    if with_url:
        parser.document_url = _URLS.get(name)
    return parser.parse(FIXTURES / f"kgm_{name}_cenik.pdf")


def _rows(name: str) -> list[tuple[str, str, float, str]]:
    return [(v.model, v.trim, v.price, v.powertrain) for v in _parse(name)]


def test_kgm_parser_reads_list_price_not_promotional_price() -> None:
    # Korando prints the promotional price ("469 900*") above the list price.
    assert _rows("korando") == [
        ("Korando", "Style", 499_900.0, "ICE"),
        ("Korando", "Smart", 529_900.0, "ICE"),
        ("Korando", "Elegant", 609_900.0, "ICE"),
        ("Korando", "Premium", 689_900.0, "ICE"),
    ]


def test_kgm_parser_separates_overlapping_struck_through_price() -> None:
    # Tivoli: "459 900" struck through, overlapping "429 900*".
    assert _rows("tivoli") == [("Tivoli", "Style", 459_900.0, "ICE")]


def test_kgm_parser_reads_two_engine_blocks_and_model_from_url() -> None:
    assert _rows("torres") == [
        ("Torres", "Club", 669_900.0, "ICE"),
        ("Torres", "Style", 719_900.0, "ICE"),
        ("Torres", "Premium", 829_900.0, "ICE"),
        ("Torres", "Club", 769_900.0, "HEV"),
        ("Torres", "Style", 819_900.0, "HEV"),
        ("Torres", "Premium", 879_900.0, "HEV"),
    ]
    assert _rows("actyon") == [
        ("Actyon", "Premium", 919_900.0, "ICE"),
        ("Actyon", "Premium", 979_900.0, "HEV"),
    ]


def test_kgm_parser_does_not_guess_a_model_it_cannot_read() -> None:
    assert _parse("torres", with_url=False) == []


def test_kgm_parser_takes_price_with_vat_for_commercial_pickup() -> None:
    # Musso Grand: "669 000" without VAT, "(809 490)" with VAT.
    assert _rows("musso_grand") == [
        ("Musso Grand", "Style 4WD", 809_490.0, "ICE"),
        ("Musso Grand", "Premium 4WD", 966_790.0, "ICE"),
    ]
    assert all("diesel" in v.variant_name for v in _parse("musso_grand"))


def test_kgm_parser_appends_standard_drive_from_equipment_table() -> None:
    variants = _parse("rexton")
    assert [(v.trim, v.price, v.variant_name.split()[-1]) for v in variants] == [
        ("Club 2WD", 899_900.0, "RWD"),
        ("Clever 4WD", 1_069_900.0, "AWD"),
        ("Premium 4WD", 1_199_900.0, "AWD"),
    ]


@pytest.mark.parametrize(
    ("name", "model", "prices"),
    [("torres_evx", "Torres EVX", [879_900.0, 959_900.0]), ("musso_ev", "Musso EV", [899_900.0, 979_900.0])],
)
def test_kgm_parser_reads_evs(name: str, model: str, prices: list[float]) -> None:
    variants = _parse(name)
    assert [(v.model, v.price, v.powertrain) for v in variants] == [(model, p, "EV") for p in prices]


def test_kgm_parser_rounds_decimal_power_in_name_only() -> None:
    variant = _parse("musso_ev")[0]
    assert variant.variant_name == "Musso EV Style 80,6 kWh/FWD - 152 kW - 207 k / 339 Nm FWD"
    assert "152,2 kW" in variant.raw_text


def test_widget_config_reads_render_call() -> None:
    html = (
        "<script>DWT.DownloadsWidget.render(document.querySelector('#id4'), "
        '{"customEnvironment":"prod","apiKey":"abc","setting":"1627","customData":{"isKgm":true}});</script>'
    )
    assert widget_config(html) == {
        "customEnvironment": "prod",
        "apiKey": "abc",
        "setting": "1627",
        "customData": {"isKgm": True},
    }
    assert widget_config("<html></html>") is None


def test_price_list_urls_skips_stock_lists_and_resolves_relative_paths() -> None:
    # Trimmed from the real download/get response of 2026-11-05.
    widget = {
        "downloadDocuments": [
            {
                "title": "Tivoli",
                "position": 1,
                "downloadItems": [
                    {
                        "title": "Zobrazit ceník skladovek",
                        "position": 1,
                        "filePath": "https://cdn.example/202611_kgm_cenik_tivoli_cz_skladove_vozy.pdf",
                    },
                    {"title": "Zobrazit nový ceník", "position": 0, "filePath": "https://cdn.example/tivoli.pdf"},
                ],
            },
            {
                "title": "Torres",
                "position": 2,
                "downloadItems": [
                    {"title": "Zobrazit ceník výprodej skladu", "position": 1, "filePath": "https://cdn.example/x.pdf"},
                    {"title": "Zobrazit ceník Torres facelift", "position": 0, "filePath": "https://cdn.example/t.pdf"},
                ],
            },
            {
                "title": "Musso EV",
                "position": 7,
                "downloadItems": [
                    {"title": "Zobrazit ceník", "position": 0, "filePath": "getImage/Downloads/c/musso_ev.pdf"}
                ],
            },
            {
                "title": "Unlisted",
                "position": 8,
                "downloadItems": [{"title": "x", "filePath": "https://cdn.example/u.pdf"}],
            },
        ]
    }
    assert price_list_urls(widget, ["Tivoli", "Torres", "Musso EV"]) == {
        "Tivoli": "https://cdn.example/tivoli.pdf",
        "Torres": "https://cdn.example/t.pdf",
        "Musso EV": "https://kgmcars.cz/getImage/Downloads/c/musso_ev.pdf",
    }
