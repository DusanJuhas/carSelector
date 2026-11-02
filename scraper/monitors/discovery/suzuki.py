"""Discoverer for auto.suzuki.cz.

Verified 2026-11-02, no bot-blocking. The "Ceníky a katalogy" page
(https://auto.suzuki.cz/prodej/ceniky-katalogy) is a client-rendered app,
but its server-sent HTML already embeds every document link in its own
state payload (JSON-escaped, hence the trailing backslash in the raw
match) - price lists on one CloudFront host, named
"<YYYYMMDD>-<model-slug>.pdf" (e.g. "20261012-s-cross-black-edition.pdf"),
catalogues ("katalog-...") and accessory lists ("prislusenstvi-...") on
the same or another host. Only date-prefixed files are price lists; if
the page ever links two dates for one slug, the newest wins.

`_SLUG_MODELS` maps a slug to the document key used in this source's
`models` - one key per DOCUMENT, like Opel's own: the Black Edition
special editions are separate price lists. SuzukiParser itself reports
the plain nameplate ("Vitara") with "Black Edition" in the trim."""

from __future__ import annotations

import re

import requests

from scraper.sources.registry import Source

from .base import BaseDiscoverer

_LISTING_URL = "https://auto.suzuki.cz/prodej/ceniky-katalogy"
_PRICE_LIST_RE = re.compile(r"(https://[a-z0-9]+\.cloudfront\.net//?)(\d{8})-([a-z0-9-]+)\.pdf")
_SLUG_MODELS = {
    "swift": "Swift",
    "vitara": "Vitara",
    "vitara-black-edition": "Vitara Black Edition",
    "s-cross": "S-Cross",
    "s-cross-black-edition": "S-Cross Black Edition",
    "e-vitara": "e Vitara",
}


class SuzukiDiscoverer(BaseDiscoverer):
    def discover(self, source: Source, *, timeout: int = 30) -> dict[str, str]:
        """Args:
            source: Registry entry whose `models` are document keys (see
                `_SLUG_MODELS`).
            timeout: HTTP request timeout in seconds.

        Returns:
            `{document_key: price_list_url}` for each of `source.models`
            linked from the listing page, newest date first - any other
            model is omitted.
        """
        response = requests.get(_LISTING_URL, timeout=timeout)
        if response.status_code != 200:
            return {}

        newest: dict[str, tuple[str, str]] = {}
        for host, date, slug in _PRICE_LIST_RE.findall(response.text):
            model = _SLUG_MODELS.get(slug)
            if model is None or model not in source.models:
                continue
            if model not in newest or date > newest[model][0]:
                newest[model] = (date, f"{host}{date}-{slug}.pdf")
        return {model: url for model, (_date, url) in newest.items()}
