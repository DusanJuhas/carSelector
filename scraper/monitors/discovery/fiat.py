"""Discoverer for Fiat's Czech price lists (fiatcz.com - fiat.cz redirects
there).

The site sits behind the same Stellantis/Akamai WAF as Opel/Peugeot/
Citroën, but with an unusual twist, verified 2026-11-02: a request with
the full browser header set `pdf_downloader.py` uses (and Opel/Peugeot
need) is answered 403, while a bare `requests.get()` with no extra
headers gets the real page - the WAF here keys on the header set, not
the TLS fingerprint. So `discover` deliberately sends no custom headers.
The PDFs themselves download with either.

"Ceníky" for passenger cars (https://www.fiatcz.com/prodej/ceniky) is
server-rendered and links every price list from one DAM folder,
"/content/dam/fiat2023/cz/ceniky/<yyyy>/<mm>/<Name>_<dd>_<mm>_<yyyy>.pdf"
(e.g. "Grande_Panda_Electric_01_10_2026.pdf", "600_01_10_2026_v2.pdf").
The document key is the name before the date ("Fiat_" prefix dropped,
underscores as spaces, `_KEY_ALIASES` for the two run-together names);
if a name is linked twice, the newest folder wins. Professional
(commercial) price lists live in a "professional/" subfolder and are
skipped, as are Topolino (a light quadricycle, not a passenger car) and
anything this source's `models` doesn't list (e.g. a stale 500X link)."""

from __future__ import annotations

import re

import requests

from scraper.sources.registry import Source

from .base import BaseDiscoverer

_BASE_URL = "https://www.fiatcz.com"
_LISTING_URL = f"{_BASE_URL}/prodej/ceniky"
_PRICE_LIST_RE = re.compile(r'href="(/content/dam/fiat2023/cz/ceniky/(\d{4})/(\d{2})/([^"/]+)\.pdf)"')
_DATE_SUFFIX_RE = re.compile(r"[_-]\d{2}[_-]\d{2}[_-]\d{4}.*$")
_KEY_ALIASES = {"TipoSedan": "Tipo Sedan", "QuboL": "Qubo L"}


def _document_key(filename: str) -> str:
    """Args:
        filename: A price list's file name without ".pdf", e.g.
            "Fiat_500_Hybrid_16_10_2026", "QuboL_14_10_2026".

    Returns:
        The document key, e.g. "500 Hybrid", "Qubo L".
    """
    name = _DATE_SUFFIX_RE.sub("", filename)
    name = re.sub(r"^Fiat[_-]", "", name).replace("_", " ").strip()
    return _KEY_ALIASES.get(name, name)


class FiatDiscoverer(BaseDiscoverer):
    def discover(self, source: Source, *, timeout: int = 30) -> dict[str, str]:
        """Args:
            source: Registry entry whose `models` are document keys (see
                `_document_key`).
            timeout: HTTP request timeout in seconds.

        Returns:
            `{document_key: price_list_url}` for each of `source.models`
            linked from the listing page (newest folder first) - any other
            document is omitted.
        """
        response = requests.get(_LISTING_URL, timeout=timeout)  # no custom headers - see module docstring
        if response.status_code != 200:
            return {}

        newest: dict[str, tuple[str, str]] = {}
        for path, year, month, filename in _PRICE_LIST_RE.findall(response.text):
            key = _document_key(filename)
            if key not in source.models:
                continue
            folder = f"{year}{month}"
            if key not in newest or folder > newest[key][0]:
                newest[key] = (folder, _BASE_URL + path)
        return {key: url for key, (_folder, url) in newest.items()}
