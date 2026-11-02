"""Parser for Honda's per-model "Ceník" price lists (verified against all
six real PDFs downloaded 2026-11-02 from honda.cz, model year 2027, valid
from 10 October 2026 - see scraper/tests/fixtures/honda_*.pdf). Covers
Jazz, Civic, HR-V, ZR-V, CR-V and Prelude - all hybrids (e:HEV), CR-V
also as a plug-in hybrid (e:PHEV).

Each document is a 2-page sheet whose price table (page 1) is one variant
per printed line:

    Elegance AWD 2.0 i-MMD Hybrid 135/184 Automatická 6,7 – 151 1 174 900

trim (with "2WD"/"AWD" where the model offers both), engine, power
"kW/hp", gearbox, WLTP consumption figure(s), CO2 g/km, then the price in
Kč without a "Kč" suffix. The price is the LAST number group, but CO2
sits right before it with only a space between ("122 744 900" is CO2 122
+ 744 900 Kč), so a plain "\\d{1,3}( \\d{3})+" would swallow the CO2
figure. `_price_from_tail` reads it from the end instead: the last two
groups of three digits, plus a single leading digit for a price of a
million or more - CO2 is always at least two digits, so a lone digit can
only be the price's own millions.

Powertrain: rows under a "Honda <model> e:PHEV" sub-heading are PHEV,
every other row is a full hybrid (HEV - Honda's i-MMD, not a mild one).
The title line ("Ceník CR-V e:HEV / e:PHEV") names both, so it doesn't
count as a sub-heading. `model` comes from that title. The cover page's
own "Platnost od 10. 10. 2026" is exactly the shape
`_pdf_layout.extract_release_date` reads, so `release_date` is set from
the document (verified on all six). Equipment and the technical-data
table below the prices aren't extracted."""

from __future__ import annotations

import re
from pathlib import Path

import pdfplumber

from ._pdf_layout import group_into_lines, line_text
from .base import BaseParser, ExtractedVariant

_TITLE_RE = re.compile(r"^Ceník\s+(?P<model>.+?)\s+e:P?HEV")
_ROW_RE = re.compile(
    r"^(?P<trim>.+?)\s+(?P<engine>\d\.\d i-MMD Hybrid)\s+(?P<kw>\d+)/(?P<hp>\d+)\s+"
    r"(?P<transmission>Automatická|Manuální)\s+(?P<tail>.+)$"
)
_DRIVE_RE = re.compile(r"\s+(2WD|AWD)$")


def _price_from_tail(tail: str) -> float | None:
    """Args:
        tail: Everything after the gearbox on a price row, e.g. "5,4 122
            744 900" or "6,7 – 151 1 174 900".

    Returns:
        The price (see module docstring), or `None` if the tail doesn't
        end in a price.
    """
    tokens = tail.split()
    if len(tokens) < 2 or not all(re.fullmatch(r"\d{3}", t) for t in tokens[-2:]):
        return None
    groups = tokens[-2:]
    if len(tokens) >= 3 and re.fullmatch(r"\d", tokens[-3]):
        groups = tokens[-3:]
    return float("".join(groups))


class HondaParser(BaseParser):
    brand = "honda"
    powertrain = "HEV"  # nominal default; e:PHEV rows are PHEV, see module docstring

    def parse(self, pdf_path: Path) -> list[ExtractedVariant]:
        """See module docstring for the row shape and the price/CO2 split.

        Args:
            pdf_path: Local path to a downloaded Honda price-list PDF.

        Returns:
            One `ExtractedVariant` per price row.
        """
        variants: list[ExtractedVariant] = []
        with pdfplumber.open(pdf_path) as pdf:
            page = pdf.pages[0]
            model = "unknown"
            powertrain = "HEV"
            for line in group_into_lines(page.extract_words()):
                text = line_text(line)
                title = _TITLE_RE.match(text)
                if title and model == "unknown":
                    model = title.group("model")
                    continue
                if "e:PHEV" in text and text.startswith("Honda"):
                    powertrain = "PHEV"
                elif "e:HEV" in text and text.startswith("Honda"):
                    powertrain = "HEV"

                match = _ROW_RE.match(text)
                price = _price_from_tail(match.group("tail")) if match else None
                if match is None or price is None:
                    continue
                trim = match.group("trim")
                drive_match = _DRIVE_RE.search(trim)
                drive = drive_match.group(1) if drive_match else ""
                trim = _DRIVE_RE.sub("", trim)
                spec = f"{match.group('engine')} {match.group('kw')} kW {drive}".strip()
                variants.append(
                    ExtractedVariant(
                        model=model,
                        trim=trim,
                        variant_name=f"{model} {trim} {spec}",
                        price=price,
                        currency="CZK",
                        source_page=page.page_number,
                        raw_text=text,
                        powertrain=powertrain,
                    )
                )
        return variants
