"""Parser for Alfa Romeo's per-model "Ceník" price lists (verified against
the real PDFs downloaded 2026-11-05 from alfaromeocz.com, valid 1-30
November 2026 - Giulia, Giulia Quadrifoglio, Stelvio, Stelvio
Quadrifoglio, Junior Ibrida, Junior Elettrica and Tonale Ibrida Plug-in
Q4; see scraper/tests/fixtures/alfa_romeo_*.pdf).

Same Stellantis CZ table as Jeep - see `parsers/_stellantis_cz.py` for
the row shape, trim headings and powertrain rules. Alfa Romeo prints only
the list price ("CENÍKOVÁ CENA"), no promotional column. `model` comes
from the page title ("ALFA ROMEO JUNIOR ELETTRICA", "GIULIA
QUADRIFOGLIO" - the Quadrifoglio documents drop the "ALFA ROMEO"
prefix). Quadrifoglio is filed as a trim of its nameplate (its own table
heading is "Quadrifoglio"), and Junior Ibrida/Elettrica both as "Junior"
- the powertrain tells them apart, the same convention as Fiat's."""

from __future__ import annotations

import re

from ._stellantis_cz import StellantisCzParser


class AlfaRomeoParser(StellantisCzParser):
    brand = "alfa-romeo"
    _title_re = re.compile(r"^(?:ALFA ROMEO\s+)?(?P<title>.+?)\s+Foto je pouze ilustrativní")
    _title_models = (
        ("GIULIA", "Giulia"),
        ("STELVIO", "Stelvio"),
        ("JUNIOR", "Junior"),
        ("TONALE", "Tonale"),
    )
