"""Discoverer for Volvo's Czech price lists.

volvocars.com/cz itself sits behind an Akamai WAF that answers every
scripted request with a 403 (verified 2026-11-02 - `requests` with a full
browser header set and `curl` alike, for the homepage and every model
page), the same situation as opel.cz's own listing page. Unlike Opel,
though, the PDFs aren't on that site: each model page's own "Otevřít PDF"
link (read out of a real browser session) points at a separate, unblocked
host with a STABLE, model-derived filename -
https://www.volvodirect.cz/cenik/<MODEL>_cenik.pdf (e.g. "XC60_cenik.pdf")
- which Volvo overwrites in place on each price change (no date or
quarter marker in the path, unlike Opel's). So nothing needs hardcoding
beyond the naming scheme: for every model in `source.models` this builds
that URL and keeps it if a HEAD request confirms it's actually a PDF.

A model with no current price list (V90, S90, V60 Cross Country, ... -
discontinued or not sold in CZ any more) gets a 403 HTML error page from
the same host instead, and is simply omitted."""

from __future__ import annotations

import requests

from scraper.sources.registry import Source

from .base import BaseDiscoverer

_PDF_URL = "https://www.volvodirect.cz/cenik/{model}_cenik.pdf"


class VolvoDiscoverer(BaseDiscoverer):
    def discover(self, source: Source, *, timeout: int = 30) -> dict[str, str]:
        """Args:
            source: Registry entry giving the models to look for - each
                name is used verbatim in the URL (spaces as "_").
            timeout: HTTP request timeout in seconds, per model.

        Returns:
            `{model: price_list_url}` for each of `source.models` whose
            URL answers with a PDF - any other model is omitted.
        """
        found: dict[str, str] = {}
        for model in source.models:
            url = _PDF_URL.format(model=model.replace(" ", "_"))
            response = requests.head(url, timeout=timeout, allow_redirects=True)
            if response.status_code == 200 and "pdf" in response.headers.get("content-type", ""):
                found[model] = url
        return found
