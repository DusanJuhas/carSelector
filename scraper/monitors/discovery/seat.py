"""Discoverer for seat.cz.

Verified 2026-11-02, server-rendered (`requests` sees the same markup a
browser does). Unlike its sister brand CUPRA's single listing page, the
SEAT listing page (https://www.seat.cz/prodej-vozu-seat/ceniky-a-katalogy)
only links one sub-page per model ("/prodej-vozu-seat/ceniky-a-katalogy/
<slug>", e.g. "nova-ibiza", "leon-sportstourer") - the actual PDF links
are on each of those, so this is a two-step fetch, like Ford's own.

On a model's sub-page the price list is a plain `<a href="/dam/files/...
.pdf" title="Ceník SEAT <Model> | SEAT">` - the `title` attribute is the
only reliable model marker (the filename itself isn't consistent:
"cenik_SEAT_Leon_MY27_1-10-2026.pdf" vs. "Cenik_Ibiza-MY27_1-10-2026.pdf"
vs. "cenik_SEAT_Leon_SP_MY27_...") and also tells the price list apart
from the same page's "Katalog SEAT <Model>" brochure link.

Ateca's own sub-page only links a "Katalog" (it's sold stock-only, same
as CUPRA's own Ateca), so it's simply never found - not an error."""

from __future__ import annotations

import re

import requests

from scraper.sources.registry import Source

from .base import BaseDiscoverer

_BASE_URL = "https://www.seat.cz"
_LISTING_PATH = "/prodej-vozu-seat/ceniky-a-katalogy"
_MODEL_PAGE_RE = re.compile(r'href="(/prodej-vozu-seat/ceniky-a-katalogy/[a-z0-9-]+)"')
_CENIK_LINK_RE = re.compile(r'<a[^>]*href="(/dam/files/[^"]+\.pdf)"[^>]*title="Ceník SEAT ([^"|]+?)\s*\|')


class SeatDiscoverer(BaseDiscoverer):
    def discover(self, source: Source, *, timeout: int = 30) -> dict[str, str]:
        """Args:
            source: Registry entry giving the models to discover (the
                listing page and each model's own sub-page are fetched -
                see module docstring).
            timeout: HTTP request timeout in seconds, per request.

        Returns:
            `{model: price_list_url}` for each of `source.models` whose
            "Ceník SEAT <Model>" link was found on its own sub-page - a
            model with no such link (e.g. Ateca) is simply omitted.
        """
        response = requests.get(_BASE_URL + _LISTING_PATH, timeout=timeout)
        if response.status_code != 200:
            return {}

        found: dict[str, str] = {}
        for page_path in dict.fromkeys(_MODEL_PAGE_RE.findall(response.text)):
            page = requests.get(_BASE_URL + page_path, timeout=timeout)
            if page.status_code != 200:
                continue
            for path, model in _CENIK_LINK_RE.findall(page.text):
                model = model.strip()
                if model in source.models and model not in found:
                    found[model] = _BASE_URL + path

        return found
