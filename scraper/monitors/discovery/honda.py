"""Discoverer for honda.cz.

Verified 2026-11-02, no bot-blocking. "Katalogy a ceníky"
(https://www.honda.cz/cars/get-a-brochure.html) is server-rendered and
links every Czech price list from one DAM folder. Two kinds sit side by
side: the regular "CZ_cenik_<Model>_MR<yy>_<yymmdd>.pdf" and a short
promotional "Akční ceník <Model> ...pdf" - only the regular one carries
the full price table HondaParser reads, so only that pattern is matched.

A model can be listed for two model years at once (verified: CR-V MR26
and MR27, Prelude MR26 and MR27) - the highest model year wins, then the
latest date."""

from __future__ import annotations

import re

import requests

from scraper.sources.registry import Source

from .base import BaseDiscoverer

_BASE_URL = "https://www.honda.cz"
_LISTING_URL = f"{_BASE_URL}/cars/get-a-brochure.html"
_PRICE_LIST_RE = re.compile(
    r'href="(/content/dam/local/czech-republic/cars/katalogy-ceniky/CZ_cenik_([A-Za-z-]+)_MR(\d+)_(\d+)\.pdf)"'
)


class HondaDiscoverer(BaseDiscoverer):
    def discover(self, source: Source, *, timeout: int = 30) -> dict[str, str]:
        """Args:
            source: Registry entry whose `models` are Honda's own model
                names as they appear in the filename ("CR-V", "Jazz").
            timeout: HTTP request timeout in seconds.

        Returns:
            `{model: price_list_url}` for each of `source.models` with a
            regular price list on the page (newest model year, then date)
            - any other model is omitted.
        """
        response = requests.get(_LISTING_URL, timeout=timeout)
        if response.status_code != 200:
            return {}

        newest: dict[str, tuple[int, str, str]] = {}
        for path, model, model_year, date in _PRICE_LIST_RE.findall(response.text):
            if model not in source.models:
                continue
            key = (int(model_year), date)
            if model not in newest or key > newest[model][:2]:
                newest[model] = (*key, _BASE_URL + path)
        return {model: url for model, (_year, _date, url) in newest.items()}
