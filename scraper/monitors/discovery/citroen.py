"""Discoverer for Citroën's Czech price lists.

citroen.cz itself answers every scripted request with a 403 (Akamai,
verified 2026-11-02 for the homepage and the price-list page alike - the
same block as fellow Stellantis brands Opel/Peugeot). Its "Ceníky a
katalogy" page (https://www.citroen.cz/nastroje/pozadat-o-brozuru.html)
is a brochure-request form, though, and the form's model picker is filled
client-side from a separate, unblocked Stellantis webforms API -
`_FORMS_URL`, found among the page's own network requests in a real
browser. One GET returns every model the picker offers, each with its
documents:

    brochurepicker.CarPicker.Model[] -> {Label, Type ("VP" passenger /
      "VU" commercial), Bodies.Body[] -> {Label, TagsId.TagId[].Id,
      Documents.Document[] -> {Title, URL}}}

The PDFs themselves are on data.citroen.cz, also unblocked.

The response also still lists discontinued models (Grand C4 Picasso,
C-Elysée, C3 Business, ...) with dead or outdated links - those carry an
empty tag, while every model currently in the picker is tagged "VP_CZ"
(passenger) or "VU_CZ" (commercial), so only "VP_CZ" bodies are read. Of
a body's documents, only the one titled exactly "Ceník a technické
parametry" is the price list - "... Cargo" (C3's commercial version),
"... PROFI" (Berlingo's), "Ceník příslušenství" (accessories) and the
brochure are skipped.

A petrol/hybrid body and its electric twin ("Nová C3" / "Nová ë-C3",
"Berlingo" / "ë-Berlingo") share one price list - bodies are keyed by
their label without the "Nový/Nová" prefix and the "ë-" electric
prefix, so both resolve to the same key ("C3", "Berlingo") and the
document is found once.

`instanceid` identifies the Czech brochure form; if Citroën ever replaces
the form, it changes and this module needs the new one (visible in the
page's network requests, as above)."""

from __future__ import annotations

import re

import requests

from scraper.sources.registry import Source

from .base import BaseDiscoverer

_FORMS_URL = "https://dpdcr-forms.citroen.com/forms/v2?instanceid=ACCZ100100030002&culture=cs-CZ&next=true"
_PASSENGER_TAG = "VP_CZ"
_PRICE_LIST_TITLE = "Ceník a technické parametry"
_PREFIX_RE = re.compile(r"^(?:Nov[áýé]\s+)?(?:ë-)?", re.IGNORECASE)


def _model_key(body_label: str) -> str:
    """Args:
        body_label: A picker body's label, e.g. "Nová ë-C3", "Nový C3
            Aircross", "ë-Berlingo".

    Returns:
        The source's model key, e.g. "C3", "C3 Aircross", "Berlingo".
    """
    return _PREFIX_RE.sub("", body_label.strip()).strip()


class CitroenDiscoverer(BaseDiscoverer):
    def discover(self, source: Source, *, timeout: int = 30) -> dict[str, str]:
        """Args:
            source: Registry entry whose `models` are the keys to look for
                (see `_model_key`).
            timeout: HTTP request timeout in seconds.

        Returns:
            `{model: price_list_url}` for each of `source.models` that the
            picker currently lists with a price list - any other model is
            omitted.
        """
        response = requests.get(_FORMS_URL, timeout=timeout)
        if response.status_code != 200:
            return {}

        models = response.json().get("brochurepicker", {}).get("CarPicker", {}).get("Model", [])
        found: dict[str, str] = {}
        for model in models:
            if model.get("Type") != "VP":
                continue
            for body in model.get("Bodies", {}).get("Body", []):
                tags = {tag.get("Id") for tag in body.get("TagsId", {}).get("TagId", [])}
                key = _model_key(body.get("Label", ""))
                if _PASSENGER_TAG not in tags or key not in source.models or key in found:
                    continue
                for document in body.get("Documents", {}).get("Document", []):
                    if document.get("Title") == _PRICE_LIST_TITLE and document.get("URL"):
                        found[key] = document["URL"]
                        break
        return found
