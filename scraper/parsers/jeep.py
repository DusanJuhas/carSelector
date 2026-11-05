"""Parser for Jeep's per-model "Ceník" price lists (verified against all
ten real PDFs downloaded 2026-11-05 from jeep.cz - Avenger (petrol/MHEV,
4xe, Electric), Compass (e-Hybrid, e-Hybrid Plug-in, Electric, 4xe
Electric) valid 1-30 November 2026, Grand Cherokee and Wrangler (petrol,
4xe) valid from 1 September 2026 - see scraper/tests/fixtures/jeep_*.pdf).

Same Stellantis CZ table as Alfa Romeo - see `parsers/_stellantis_cz.py`
for the row shape, trim headings and powertrain rules. `model` comes from
the page title ("NOVÝ JEEP COMPASS E-HYBRID PLUG-IN", "JEEP WRANGLER
4XE"); every powertrain twin keeps its nameplate (Avenger Electric ->
"Avenger", Wrangler 4xe -> "Wrangler"), the same convention as Fiat's and
Opel's, and the powertrain tells them apart. Grand Cherokee and Wrangler
4xe are PHEV ("benzín/PHEV", "Benzín/Elektřina"); Avenger 4xe's "1.2 Turbo
e-Hybrid 145k 4xe" is Stellantis's 48V hybrid with an extra rear e-motor
("Benzín" fuel), so MHEV like the other e-Hybrids."""

from __future__ import annotations

import re

from ._stellantis_cz import StellantisCzParser


class JeepParser(StellantisCzParser):
    brand = "jeep"
    _title_re = re.compile(r"^(?:NOVÝ\s+)?JEEP\s+(?P<title>.+?)\s+Foto je pouze ilustrativní")
    _title_models = (
        ("GRAND CHEROKEE", "Grand Cherokee"),
        ("WRANGLER", "Wrangler"),
        ("COMPASS", "Compass"),
        ("AVENGER", "Avenger"),
    )
