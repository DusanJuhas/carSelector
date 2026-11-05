"""Discoverer for KGM's (formerly SsangYong) Czech price lists
(kgmcars.cz - ssangyong.cz redirects there).

Verified 2026-11-05. "Ceníky" (https://kgmcars.cz/nove-vozy/ceniky/)
doesn't link its PDFs in its HTML: the list is rendered client-side by a
third-party dealer-site widget (Carussel DWT), embedded as

    DWT.DownloadsWidget.render(document.querySelector('#id4'),
        {"customEnvironment":"prod","apiKey":"...","setting":"1627", ...});

and fed by that widget's JSON API. `discover` does what the page's own
script does, so the key and widget id are read from the page every run
rather than hard-coded: log in with the page's public `apiKey`
(`GET <api>/auth/v1/auth/login?apiKey=...&origin=kgmcars.cz`, which
returns a short-lived bearer token and the API base URL), then fetch
`GET <api>/widget/v1/download/get?setting=<setting>`. Its
`downloadDocuments` are one entry per model (`title` "Korando", "Torres
EVX", ...), each with one or more `downloadItems` whose `filePath` is the
PDF - absolute on the widget's CDN, or relative to kgmcars.cz
("getImage/Downloads/...").

A model can list a stock-car clearance list next to its regular one
("Zobrazit ceník skladovek", "ceník výprodej skladu"); those are skipped,
and of the rest the first by `position` is taken.

kgmcars.cz answers the default `python-requests` User-Agent with a 403
(any browser-like one works), so the listing page is fetched with one;
the API and both PDF hosts don't care."""

from __future__ import annotations

import json
import re
from urllib.parse import urljoin

import requests

from scraper.sources.registry import Source

from .base import BaseDiscoverer

_SITE_URL = "https://kgmcars.cz/"
_LISTING_URL = urljoin(_SITE_URL, "nove-vozy/ceniky/")
_API_URL = "https://module.api.prod.opel.carusseldwt.com"
_ORIGIN = "kgmcars.cz"
_WIDGET_RE = re.compile(r"DWT\.DownloadsWidget\.render\([^,]+,\s*")
_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)
_STOCK_MARKER = "sklad"


def widget_config(html: str) -> dict | None:
    """Args:
        html: The "Ceníky" page's HTML.

    Returns:
        The `DownloadsWidget` render call's config object (with `apiKey`
        and `setting`), or `None` if the page has no such call.
    """
    match = _WIDGET_RE.search(html)
    if match is None:
        return None
    config, _end = json.JSONDecoder().raw_decode(html, match.end())
    return config


def price_list_urls(widget: dict, models: list[str]) -> dict[str, str]:
    """Args:
        widget: The `download/get` API response.
        models: The model titles to keep (`source.models`).

    Returns:
        `{model: absolute_pdf_url}` - per model, the first non-stock item
        by `position` (see module docstring); models in `models` with no
        such item are omitted.
    """
    found: dict[str, str] = {}
    for document in sorted(widget.get("downloadDocuments", []), key=lambda d: d.get("position", 0)):
        model = (document.get("title") or "").strip()
        if model not in models or model in found:
            continue
        for item in sorted(document.get("downloadItems", []), key=lambda i: i.get("position", 0)):
            text = " ".join(str(item.get(key) or "") for key in ("title", "description", "filePath")).lower()
            path = item.get("filePath")
            if path and _STOCK_MARKER not in text:
                found[model] = urljoin(_SITE_URL, path)
                break
    return found


class KgmDiscoverer(BaseDiscoverer):
    def discover(self, source: Source, *, timeout: int = 30) -> dict[str, str]:
        """Args:
            source: Registry entry whose `models` are the widget's model
                titles ("Korando", "Torres EVX", ...).
            timeout: HTTP request timeout in seconds, per request.

        Returns:
            `{model: price_list_url}` for each of `source.models` the
            widget lists a regular price list for - any other model is
            omitted.
        """
        page = requests.get(_LISTING_URL, headers={"User-Agent": _USER_AGENT}, timeout=timeout)
        if page.status_code != 200:
            return {}
        config = widget_config(page.text)
        if config is None:
            return {}

        login = requests.get(
            f"{_API_URL}/auth/v1/auth/login",
            params={"apiKey": config["apiKey"], "origin": _ORIGIN},
            timeout=timeout,
        )
        if login.status_code != 200:
            return {}
        auth = login.json()
        api_url = auth.get("apiUrl") or _API_URL
        widget = requests.get(
            f"{api_url}/widget/v1/download/get",
            params={"setting": config["setting"]},
            headers={"Authorization": f"Bearer {auth['token']}"},
            timeout=timeout,
        )
        if widget.status_code != 200:
            return {}
        return price_list_urls(widget.json(), source.models)
