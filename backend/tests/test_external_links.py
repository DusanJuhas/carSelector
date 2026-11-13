"""Unit tests for app/services/external_links.py."""

from urllib.parse import parse_qs, urlsplit

from app.services.external_links import BRAND_WEBSITES, build_external_links, manufacturer_url, review_video_url


def test_manufacturer_url_known_brand():
    assert manufacturer_url("skoda") == "https://www.skoda-auto.cz"


def test_manufacturer_url_unknown_brand_is_none():
    assert manufacturer_url("trabant") is None


def test_every_brand_website_is_https():
    assert all(url.startswith("https://") for url in BRAND_WEBSITES.values())


def _search_query(url: str) -> str:
    parts = urlsplit(url)
    assert f"{parts.scheme}://{parts.netloc}{parts.path}" == "https://www.youtube.com/results"
    return parse_qs(parts.query)["search_query"][0]


def test_review_video_url_czech_keyword_and_diacritics():
    assert _search_query(review_video_url("Škoda", "Kodiaq")) == "Škoda Kodiaq recenze"


def test_review_video_url_english_and_unknown_language():
    assert _search_query(review_video_url("Mazda", "CX-5", language="en")) == "Mazda CX-5 review"
    assert _search_query(review_video_url("Mazda", "CX-5", language="de")) == "Mazda CX-5 recenze"


def test_build_external_links():
    links = build_external_links("mazda", "Mazda", "CX-5", language="en")
    assert links.manufacturer_url == "https://www.mazda.cz"
    assert _search_query(links.review_video_url) == "Mazda CX-5 review"
