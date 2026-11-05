"""Discoverer for Alfa Romeo's Czech price lists (alfaromeocz.com -
alfaromeo.cz redirects there).

Verified 2026-11-05: "Ceníky" (https://www.alfaromeocz.com/prodej/ceniky)
links every price list from "/content/dam/alfa/cz/download-center/<yyyy>/
<mm>/", e.g. "AR_Junior_Elettrica_01_11_2026.pdf", "AR_Giulia_QV_01_11_2026
.pdf". Keys drop the "AR_"/"AlfaRomeo_" prefix; "QV" is spelled out as
"Quadrifoglio". Stock-car lists live in a "skladove-vozy/" subfolder and
are skipped. See `_stellantis_cz.py` for the rest.

The plain "AR_Tonale_..." file linked on 2026-11-05 actually contains the
Junior Elettrica price list (an upload mistake on the importer's side), so
"Tonale" is left out of this source's `models` for now - see
`sources.yaml`."""

from __future__ import annotations

import re

from ._stellantis_cz import StellantisCzDiscoverer


class AlfaRomeoDiscoverer(StellantisCzDiscoverer):
    _base_url = "https://www.alfaromeocz.com"
    _listing_path = "/prodej/ceniky"
    _price_list_re = re.compile(r'"(/content/dam/alfa/cz/download-center/(\d{4})/(\d{2})/(?:[^"]+/)?([^"/]+)\.pdf)"')
    _prefix_re = re.compile(r"^(?:AR|AlfaRomeo)_")
    _skip_re = re.compile(r"/skladove-vozy/")
    _key_aliases = {"Giulia QV": "Giulia Quadrifoglio", "Stelvio QV": "Stelvio Quadrifoglio"}
