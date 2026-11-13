"""Links from a vehicle's detail to outside sources: the manufacturer's own
Czech website and video reviews of the model.

Neither comes from the scraped price lists, so both are derived here
rather than stored: the manufacturer link is a curated per-brand homepage
(hosts taken from the price-list sources in `scraper/config/sources.yaml`),
and the review link is a YouTube search for "<brand> <model>" plus a
review keyword in the reader's language - a search rather than one fixed
video, so it never goes stale or points at the wrong generation.
"""

from urllib.parse import urlencode

from app.schemas.vehicle import ExternalLinks

# Brand slug (`brands.slug`, same keys as `scripts/import_scraper_data.py`'s
# BRAND_NAMES) -> the manufacturer's Czech-market homepage.
BRAND_WEBSITES: dict[str, str] = {
    "alfa-romeo": "https://www.alfaromeocz.com",
    "audi": "https://www.audi.cz",
    "bmw": "https://www.bmw.cz",
    "citroen": "https://www.citroen.cz",
    "cupra": "https://www.cupraofficial.cz",
    "dacia": "https://www.dacia.cz",
    "fiat": "https://www.fiatcz.com",
    "ford": "https://www.ford.cz",
    "honda": "https://www.honda.cz",
    "hyundai": "https://www.hyundai.com/cz/",
    "jeep": "https://www.jeep.cz",
    "kgm": "https://kgmcars.cz",
    "kia": "https://www.kia.com/cz/",
    "lexus": "https://www.lexus.cz",
    "mazda": "https://www.mazda.cz",
    "mercedes-benz": "https://www.mercedes-benz.cz",
    "mg": "https://www.mgmotor-czech.cz",
    "mitsubishi": "https://www.mitsubishi-motors.cz",
    "nissan": "https://www.nissan.cz",
    "opel": "https://www.opel.cz",
    "peugeot": "https://www.peugeot.cz",
    "renault": "https://www.renault.cz",
    "seat": "https://www.seat.cz",
    "skoda": "https://www.skoda-auto.cz",
    "subaru": "https://www.subaru.cz",
    "suzuki": "https://auto.suzuki.cz",
    "tesla": "https://www.tesla.com/cs_cz",
    "toyota": "https://www.toyota.cz",
    "volkswagen": "https://www.volkswagen.cz",
    "volvo": "https://www.volvocars.com/cz/",
}

# Review keyword appended to the YouTube search, per UI language.
_REVIEW_KEYWORDS: dict[str, str] = {"cs": "recenze", "en": "review"}
_DEFAULT_LANGUAGE = "cs"

_YOUTUBE_SEARCH_URL = "https://www.youtube.com/results"


def manufacturer_url(brand_slug: str) -> str | None:
    """Args:
        brand_slug: The vehicle's `brands.slug`.

    Returns:
        The manufacturer's Czech homepage, or `None` for a brand without
        a curated entry in `BRAND_WEBSITES`.
    """
    return BRAND_WEBSITES.get(brand_slug)


def review_video_url(brand: str, model: str, *, language: str = _DEFAULT_LANGUAGE) -> str:
    """Args:
        brand: Brand display name, e.g. "Škoda".
        model: Model display name, e.g. "Kodiaq".
        language: UI language code (`"cs"`/`"en"`) picking the review
            keyword; unknown codes fall back to Czech.

    Returns:
        A YouTube search URL for video reviews of the model.
    """
    keyword = _REVIEW_KEYWORDS.get(language, _REVIEW_KEYWORDS[_DEFAULT_LANGUAGE])
    return f"{_YOUTUBE_SEARCH_URL}?{urlencode({'search_query': f'{brand} {model} {keyword}'})}"


def build_external_links(
    brand_slug: str, brand: str, model: str, *, language: str = _DEFAULT_LANGUAGE
) -> ExternalLinks:
    """Args:
        brand_slug: The vehicle's `brands.slug`.
        brand: Brand display name.
        model: Model display name.
        language: UI language code for the review search keyword.

    Returns:
        Both outside links for one model.
    """
    return ExternalLinks(
        manufacturer_url=manufacturer_url(brand_slug),
        review_video_url=review_video_url(brand, model, language=language),
    )
