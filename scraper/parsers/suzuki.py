"""Parser for Suzuki's per-model "Akční ceník" price lists (verified against
all six real PDFs downloaded 2026-11-02 from auto.suzuki.cz's CloudFront
asset host, valid from 12 October 2026 - see scraper/tests/fixtures/
suzuki_*.pdf). Covers Swift, Vitara, S-Cross (each petrol model also as a
separate "Black Edition" document) and e Vitara.

Every document's price table ("Motorizace", page 1) is one variant per
printed line, the trim embedded in the row:

    1.4 BoosterJet PREMIUM 6AT 4×4 AllGrip 81 683 900 Kč
    1.4 BoosterJet ELEGANCE PANORAMA* Black Edition 6AT 4×4 AllGrip 81 733 900 Kč
    61 kWh ELEGANCE 4×4 135 1 027 500 Kč 50 000 Kč 977 500 Kč

engine, trim, gearbox, drive, power (kW), then the price. Where a
document also prints a bonus and a promotional price ("STANDARDNÍ CENA /
BONUS / AKČNÍ CENA" - Swift, e Vitara), `price` is the first one, the
standard list price, the same convention as every other brand here. The
"*" after PANORAMA is a footnote mark (panoramic roof) and is dropped.

The model name is NOT in the extractable text of every document (Vitara's
and e Vitara's own names are part of their cover artwork; only S-Cross
and Swift print theirs as text), so it is inferred, in this order:
a battery capacity ("61 kWh") in the row -> "e Vitara" (Suzuki's only EV
here); "S-Cross" anywhere in the document -> "S-Cross"; a DualJet engine
(Swift's own, "1.2 DualJet") -> "Swift"; otherwise a BoosterJet engine ->
"Vitara". A future Suzuki model would need a rule of its own here.

Every petrol engine here is a mild hybrid (the documents' own spec
tables: "1.2 HYBRID ... Mild-hybridní systém", "1.4 BOOSTERJET 48V SHVS
MILD HYBRID"), so those rows are MHEV; battery rows are EV. The
effective date is written out ("Platnost od 12. října 2026"), which
`_pdf_layout.extract_release_date` doesn't parse, so `release_date`
stays None. Equipment isn't extracted."""

from __future__ import annotations

import re
from pathlib import Path

import pdfplumber

from ._pdf_layout import group_into_lines, line_text
from .base import BaseParser, ExtractedVariant

_PRICE = r"(?P<price>\d{1,3}(?: \d{3})+)\s*Kč"
_ICE_ROW_RE = re.compile(
    r"^(?P<engine>\d\.\d \S+)\s+(?P<trim>.+?)\s+(?P<transmission>\d?MT|\d?AT|CVT)\s+"
    r"(?P<drive>4×[24](?: AllGrip)?)\s+(?P<kw>\d+)\s+" + _PRICE
)
_EV_ROW_RE = re.compile(r"^(?P<battery>\d+ kWh)\s+(?P<trim>.+?)\s+(?P<drive>4×[24])\s+(?P<kw>\d+)\s+" + _PRICE)


def _model_for(document_text: str, engine: str | None) -> str:
    """Args:
        document_text: The whole document's extracted text.
        engine: The row's engine ("1.4 BoosterJet"), or `None` for a
            battery (EV) row.

    Returns:
        The model, by the inference rules in the module docstring.
    """
    if engine is None:
        return "e Vitara"
    if "S-Cross" in document_text:
        return "S-Cross"
    if "DualJet" in engine:
        return "Swift"
    return "Vitara"


class SuzukiParser(BaseParser):
    brand = "suzuki"
    powertrain = "MHEV"  # nominal default; battery rows are EV, see module docstring

    def parse(self, pdf_path: Path) -> list[ExtractedVariant]:
        """See module docstring for the row shape and model inference.

        Args:
            pdf_path: Local path to a downloaded Suzuki price-list PDF.

        Returns:
            One `ExtractedVariant` per row of the "Motorizace" table.
        """
        variants: list[ExtractedVariant] = []
        with pdfplumber.open(pdf_path) as pdf:
            document_text = "\n".join(page.extract_text() or "" for page in pdf.pages)
            for page in pdf.pages:
                for line in group_into_lines(page.extract_words()):
                    text = line_text(line)
                    variant = self._parse_row(text, document_text, page.page_number)
                    if variant is not None:
                        variants.append(variant)
        return variants

    @staticmethod
    def _parse_row(text: str, document_text: str, page_number: int) -> ExtractedVariant | None:
        """Args:
            text: One printed line.
            document_text: The whole document's text (for the model).
            page_number: 1-based page the line is on.

        Returns:
            The row's variant, or `None` if the line isn't a price row.
        """
        ice = _ICE_ROW_RE.match(text)
        ev = None if ice else _EV_ROW_RE.match(text)
        match = ice or ev
        if match is None:
            return None

        trim = " ".join(match.group("trim").replace("*", " ").split())
        if ice:
            engine = ice.group("engine")
            spec = f"{engine} {ice.group('kw')} kW {ice.group('transmission')} {ice.group('drive')}"
            powertrain = "MHEV"
            model = _model_for(document_text, engine)
        else:
            spec = f"{ev.group('battery')} {ev.group('kw')} kW {ev.group('drive')}"
            powertrain = "EV"
            model = _model_for(document_text, None)

        return ExtractedVariant(
            model=model,
            trim=trim,
            variant_name=f"{model} {trim} {spec}",
            price=float(match.group("price").replace(" ", "")),
            currency="CZK",
            source_page=page_number,
            raw_text=text,
            powertrain=powertrain,
        )
