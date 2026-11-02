"""Discoverer for nissan.cz.

Verified 2026-11-02, no bot-blocking. Nissan's Czech price lists live in
one CDN folder (www-europe.nissan-cdn.net/content/dam/Nissan/cz/
brochures/Pricelists/). Two pages link into it, and they disagree: the
"Brožury a ceníky" page (/brozury-y-ceniky.html) still links outdated
files (Qashqai 2024, the previous X-Trail), while the homepage's own
model menu links the current ones (Qashqai 2026, X-Trail 2026 plus its
Summer Edition) - so the homepage is the source here.

File names follow no pattern ("MICRA_2025_CZ.pdf", "NEW_JUKE_retail_
pricelist_CZE_MY24.pdf", "Qashqai-Pricelist_CZ_2026.pdf", "X-TRAIL-2026-
SUMMER-EDITION.pdf"), so `_document_key` recognises the model in each
name; Interstar/Townstar (commercial vehicles) aren't matched. If a key
is linked more than once, the file whose name carries the highest year
wins."""

from __future__ import annotations

import re

import requests

from scraper.sources.registry import Source

from .base import BaseDiscoverer

_HOMEPAGE = "https://www.nissan.cz/"
_PRICE_LIST_RE = re.compile(
    r"//(www-europe\.nissan-cdn\.net/content/dam/Nissan/cz/brochures/Pricelists/([^\"']+)\.pdf)"
)
_YEAR_RE = re.compile(r"20\d{2}")


def _document_key(filename: str) -> str | None:
    """Args:
        filename: A price list's file name without ".pdf".

    Returns:
        The document key ("Micra", "Juke", "Qashqai", "X-Trail",
        "X-Trail Summer Edition"), or `None` for any other model.
    """
    upper = filename.upper()
    if "X-TRAIL" in upper:
        return "X-Trail Summer Edition" if "SUMMER" in upper else "X-Trail"
    for name in ("Micra", "Juke", "Qashqai"):
        if name.upper() in upper:
            return name
    return None


class NissanDiscoverer(BaseDiscoverer):
    def discover(self, source: Source, *, timeout: int = 30) -> dict[str, str]:
        """Args:
            source: Registry entry whose `models` are document keys (see
                `_document_key`).
            timeout: HTTP request timeout in seconds.

        Returns:
            `{document_key: price_list_url}` for each of `source.models`
            linked from the homepage - any other document is omitted.
        """
        response = requests.get(_HOMEPAGE, timeout=timeout)
        if response.status_code != 200:
            return {}

        newest: dict[str, tuple[int, str]] = {}
        for path, filename in _PRICE_LIST_RE.findall(response.text):
            key = _document_key(filename)
            if key is None or key not in source.models:
                continue
            years = [int(y) for y in _YEAR_RE.findall(filename)]
            year = max(years) if years else 0
            if key not in newest or year > newest[key][0]:
                newest[key] = (year, "https://" + path)
        return {key: url for key, (_year, url) in newest.items()}
