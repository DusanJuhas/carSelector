"""Discoverer for subaru.cz.

Verified 2026-11-02, no bot-blocking. "Ceníky" (https://www.subaru.cz/
ceniky.html) links one page per model ("forester-cenik.html",
"nova-solterra-cenik.html", "outback-ceniky.html", ...), and each of
those links that model's current price list as
"https://www.subaru.cz/download/ceniky/<year>/<name>.pdf" - two-step
fetch, like SEAT's. The PDF name itself isn't a reliable key (it changes
with each promotion, "akcni-cenik-..." vs. "cenik-...", and has typos -
"cenik-subaru-e-otback.pdf"), so the model is taken from the model
page's own name (`_PAGE_MODELS`).

Crosstrek's and Outback's pages currently link no price list (verified
2026-11-02), so those two are simply not found."""

from __future__ import annotations

import re

import requests

from scraper.sources.registry import Source

from .base import BaseDiscoverer

_BASE_URL = "https://www.subaru.cz/"
_LISTING_URL = f"{_BASE_URL}ceniky.html"
_MODEL_PAGE_RE = re.compile(r'href="([a-z-]+-ceniky?\.html)"')
_PRICE_LIST_RE = re.compile(r'href="(https://www\.subaru\.cz/download/ceniky/[^"]+\.pdf)"')
_PAGE_MODELS = {
    "impreza-cenik.html": "Impreza",
    "crosstrek-ceniky.html": "Crosstrek",
    "forester-cenik.html": "Forester",
    "outback-ceniky.html": "Outback",
    "e-outback-cenik.html": "e-Outback",
    "nova-solterra-cenik.html": "Solterra",
    "uncharted-cenik.html": "Uncharted",
}


class SubaruDiscoverer(BaseDiscoverer):
    def discover(self, source: Source, *, timeout: int = 30) -> dict[str, str]:
        """Args:
            source: Registry entry giving the models to look for.
            timeout: HTTP request timeout in seconds, per request.

        Returns:
            `{model: price_list_url}` for each of `source.models` whose
            model page links a price list - any other model is omitted.
        """
        response = requests.get(_LISTING_URL, timeout=timeout)
        if response.status_code != 200:
            return {}

        found: dict[str, str] = {}
        for page_name in dict.fromkeys(_MODEL_PAGE_RE.findall(response.text)):
            model = _PAGE_MODELS.get(page_name)
            if model is None or model not in source.models or model in found:
                continue
            page = requests.get(_BASE_URL + page_name, timeout=timeout)
            if page.status_code != 200:
                continue
            match = _PRICE_LIST_RE.search(page.text)
            if match:
                found[model] = match.group(1)
        return found
