"""Shared discoverer for the Stellantis Czech importer's brand sites (Jeep,
Alfa Romeo - see `jeep.py`, `alfa_romeo.py`; `fiat.py` predates this
module and follows the same pattern on its own).

Each site has one server-rendered listing page linking every current
price list from an AEM DAM folder, "/content/dam/<brand>/cz/<...>/<yyyy>/
<mm>/<Name>_<dd>_<mm>_<yyyy>.pdf". The document key is the file name
with the date suffix and the brand prefix dropped and underscores read
as spaces (plus per-brand `_key_aliases` for run-together names); if a
key is linked twice, the newest folder wins. Stock-car ("skladové vozy")
lists are skipped by each brand's own `_skip_re`.

Like Fiat's, these sites sit behind the Stellantis Akamai WAF, which
(verified 2026-11-05 on jeep.cz) answers the full browser header set
`pdf_downloader.py` uses with a 403 but serves a bare `requests.get()` -
so `discover` sends no custom headers. The PDFs themselves download with
either."""

from __future__ import annotations

import re

import requests

from scraper.sources.registry import Source

from .base import BaseDiscoverer

_DATE_SUFFIX_RE = re.compile(r"[_-]\d{2}[_-]\d{2}[_-]\d{4}.*$")


class StellantisCzDiscoverer(BaseDiscoverer):
    """Base for one brand. Subclasses set `_base_url`, `_listing_path`,
    `_price_list_re` (groups: path, year, month, file name without
    ".pdf"), `_prefix_re` (brand prefix to drop from the file name),
    `_skip_re` (paths to ignore) and `_key_aliases`."""

    _base_url: str
    _listing_path: str
    _price_list_re: re.Pattern[str]
    _prefix_re: re.Pattern[str]
    _skip_re: re.Pattern[str]
    _key_aliases: dict[str, str] = {}

    def document_key(self, filename: str) -> str:
        """Args:
            filename: A price list's file name without ".pdf", e.g.
                "Novy_Jeep_Avenger_Electric_01-11-2026".

        Returns:
            The document key, e.g. "Avenger Electric".
        """
        name = _DATE_SUFFIX_RE.sub("", filename)
        name = self._prefix_re.sub("", name).replace("_", " ").strip()
        return self._key_aliases.get(name, name)

    def discover(self, source: Source, *, timeout: int = 30) -> dict[str, str]:
        """Args:
            source: Registry entry whose `models` are document keys (see
                `document_key`).
            timeout: HTTP request timeout in seconds.

        Returns:
            `{document_key: price_list_url}` for each of `source.models`
            linked from the listing page (newest folder first) - any other
            document is omitted.
        """
        response = requests.get(self._base_url + self._listing_path, timeout=timeout)  # no custom headers
        if response.status_code != 200:
            return {}

        newest: dict[str, tuple[str, str]] = {}
        for path, year, month, filename in self._price_list_re.findall(response.text):
            if self._skip_re.search(path):
                continue
            key = self.document_key(filename)
            if key not in source.models:
                continue
            folder = f"{year}{month}"
            if key not in newest or folder > newest[key][0]:
                newest[key] = (folder, self._base_url + path)
        return {key: url for key, (_folder, url) in newest.items()}
