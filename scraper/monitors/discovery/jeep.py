"""Discoverer for Jeep's Czech price lists (jeep.cz).

Verified 2026-11-05: "Dokumenty" (https://www.jeep.cz/dokumenty) links
every price list from "/content/dam/jeep/cz/pricelist/<yyyy>/<mm>/", e.g.
"Novy_Jeep_Avenger_4xe_01-11-2026.pdf", "Jeep_WranglerPHEV_01-09-2026.pdf".
Keys drop the "Novy_Jeep_"/"Jeep_" prefix ("Avenger 4xe", "Compass
e-Hybrid Plug-in"); `_KEY_ALIASES` splits the run-together names.
"sklad_..." files are stock-car lists (a subset of the regular list at
lower prices) and are skipped. See `_stellantis_cz.py` for the rest."""

from __future__ import annotations

import re

from ._stellantis_cz import StellantisCzDiscoverer


class JeepDiscoverer(StellantisCzDiscoverer):
    _base_url = "https://www.jeep.cz"
    _listing_path = "/dokumenty"
    _price_list_re = re.compile(r'"(/content/dam/jeep/cz/pricelist/(\d{4})/(\d{2})/([^"/]+)\.pdf)"')
    _prefix_re = re.compile(r"^(?:Novy_)?Jeep_")
    _skip_re = re.compile(r"/sklad_")
    _key_aliases = {
        "GrandCherokee": "Grand Cherokee",
        "WranglerICE": "Wrangler",
        "WranglerPHEV": "Wrangler 4xe",
    }
