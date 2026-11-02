"""Discoverer for mitsubishi-motors.cz.

Verified 2026-11-02, server-rendered, no bot-blocking (`requests` gets a
plain 200). The listing page (https://www.mitsubishi-motors.cz/nakup-vozu/
ceniky-a-katalogy/) links one sub-page per model (".../74-asx/",
".../76-outlander-phev-4x4/", ...), and each of those links its PDFs as
`<a href="/images/mod_catalog/pdf/...pdf" onclick="gtag('event', 'Download
file', {'event_category' : 'Pricelist', 'event_label' : 'Ceník ASX
MY26'});">` - two-step fetch, like SEAT's own.

The `event_category` tells a price list ("Pricelist") from a brochure
("Brochure"), and the `event_label` is the only reliable name for the
document (filenames carry a random numeric prefix that changes with every
upload). A model page can link several price lists - ASX's has both the
regular one and the "Limited" special edition, Outlander PHEV's has four
(regular, "Black Edition", "Diamond", "25 let") - so, like Opel's own,
this source's `models` lists one key per DOCUMENT: the label with "Ceník"
and the model-year marker ("MY26", which can sit mid-label: "Ceník ASX
MY25 Limited") removed, e.g. "ASX", "ASX Limited", "Outlander PHEV Black
Edition", "Colt Hybrid". MitsubishiParser then normalizes each document's
model back to the nameplate ("ASX", "Outlander PHEV", "Colt").

Some special editions also have a model sub-page of their own that links
the same price list again (sometimes an older upload of it - verified:
"Black Edition" is linked as both a "_1126" and a "_1026" file) - the
first link found wins, and the listing page's own order puts the main
model pages first."""

from __future__ import annotations

import re

import requests

from scraper.sources.registry import Source

from .base import BaseDiscoverer

_BASE_URL = "https://www.mitsubishi-motors.cz"
_LISTING_URL = f"{_BASE_URL}/nakup-vozu/ceniky-a-katalogy/"
_MODEL_PAGE_RE = re.compile(r'href="(https://www\.mitsubishi-motors\.cz/nakup-vozu/ceniky-a-katalogy/\d+-[a-z0-9-]+/)"')
_PRICELIST_LINK_RE = re.compile(
    r"href=\"(/images/mod_catalog/pdf/[^\"]+\.pdf)\"[^>]*"
    r"'event_category'\s*:\s*'Pricelist',\s*'event_label'\s*:\s*'([^']+)'"
)
_MODEL_YEAR_RE = re.compile(r"\s*\bMY\d+\b")


def _document_key(label: str) -> str:
    """Args:
        label: A price-list link's `event_label`, e.g. "Ceník ASX MY25
            Limited".

    Returns:
        The document key used in `source.models`, e.g. "ASX Limited".
    """
    return _MODEL_YEAR_RE.sub("", label.removeprefix("Ceník ")).strip()


class MitsubishiDiscoverer(BaseDiscoverer):
    def discover(self, source: Source, *, timeout: int = 30) -> dict[str, str]:
        """Args:
            source: Registry entry whose `models` are document keys (see
                module docstring).
            timeout: HTTP request timeout in seconds, per request.

        Returns:
            `{document_key: price_list_url}` for each of `source.models`
            found on a model sub-page - any other is omitted.
        """
        response = requests.get(_LISTING_URL, timeout=timeout)
        if response.status_code != 200:
            return {}

        found: dict[str, str] = {}
        for page_url in dict.fromkeys(_MODEL_PAGE_RE.findall(response.text)):
            page = requests.get(page_url, timeout=timeout)
            if page.status_code != 200:
                continue
            for path, label in _PRICELIST_LINK_RE.findall(page.text):
                key = _document_key(label)
                if key in source.models and key not in found:
                    found[key] = _BASE_URL + path

        return found
