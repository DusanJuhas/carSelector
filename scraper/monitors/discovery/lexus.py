"""Discoverer for lexus.cz.

Verified 2026-11-02, no bot-blocking. "Ceníky" (https://www.lexus.cz/
pricelists) is server-rendered and links every Czech price list on
content.lexus-ce.com, one PDF per model or, for NX and RX, per engine:
"CZ_NX350_MY26.pdf", "CZ_RX450h_MY27.pdf", "cenik_UX_300_MY26_CZ.pdf",
"CZ_ES26_cenik.pdf", "RZ-CZ.pdf", "cenik_cz_LM.pdf". The file names
follow no single pattern, so `_document_key` reads the family and, where
present, the engine number out of each name ("NX 350", "RX 450h", "UX
300", "ES", "RZ", "LBX", "LM") - the document keys this source's `models`
lists. Non-price-list PDFs on the page (competition rules) have no family
and are skipped.

A model can be listed for two model years at once (verified: all three
RX documents as both MY26 and MY27) - the highest "MY" wins; a name
without "MY" counts as the oldest."""

from __future__ import annotations

import re

import requests

from scraper.sources.registry import Source

from .base import BaseDiscoverer

_LISTING_URL = "https://www.lexus.cz/pricelists"
_PDF_RE = re.compile(r"https://content\.lexus-ce\.com/lexus_cz_sk/([^\"'?#]+)\.pdf")
_KEY_RE = re.compile(r"(?<![A-Za-z])(LBX|UX|NX|RX|RZ|ES|LM)(?:[ _-]?(\d{3}[a-z]?\+?))?(?![A-Za-z])")
_MODEL_YEAR_RE = re.compile(r"MY(\d+)")


def _document_key(filename: str) -> str | None:
    """Args:
        filename: A PDF's file name without ".pdf", e.g. "CZ_RX450h_MY27".

    Returns:
        The document key ("RX 450h"), or `None` for a file that names no
        Lexus family.
    """
    match = _KEY_RE.search(filename)
    if match is None:
        return None
    family, engine = match.groups()
    return f"{family} {engine}" if engine else family


class LexusDiscoverer(BaseDiscoverer):
    def discover(self, source: Source, *, timeout: int = 30) -> dict[str, str]:
        """Args:
            source: Registry entry whose `models` are document keys (see
                `_document_key`).
            timeout: HTTP request timeout in seconds.

        Returns:
            `{document_key: price_list_url}` for each of `source.models`
            linked from the page (newest model year first) - any other
            document is omitted.
        """
        response = requests.get(_LISTING_URL, timeout=timeout)
        if response.status_code != 200:
            return {}

        newest: dict[str, tuple[int, str]] = {}
        for filename in set(_PDF_RE.findall(response.text)):
            key = _document_key(filename)
            if key is None or key not in source.models:
                continue
            year_match = _MODEL_YEAR_RE.search(filename)
            year = int(year_match.group(1)) if year_match else 0
            if key not in newest or year > newest[key][0]:
                newest[key] = (year, f"https://content.lexus-ce.com/lexus_cz_sk/{filename}.pdf")
        return {key: url for key, (_year, url) in newest.items()}
