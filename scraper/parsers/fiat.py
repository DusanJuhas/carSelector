"""Parser for Fiat's per-model "Ceník" price lists (verified against all
nine real PDFs downloaded 2026-11-02 from fiatcz.com, valid 1-31 October
2026 - see scraper/tests/fixtures/fiat_*.pdf). Covers 500 (Hybrid and
electric "500e"), 600 (petrol/hybrid and electric "600e"), Grande Panda
(petrol/hybrid and Electric), Pandina, Tipo Sedan and Qubo L.

Every document has one "CENÍKOVÉ (A AKČNÍ) CENY" page laid out as a trim
heading on its own line, then one variant per line, anchored on Fiat's
own order code ("364.B23.3"):

    Icon
    364.J23.3 1.2 Turbo Hybrid 110k 81kW/110k Benzín 6st. automatická 649 900 Kč 574 900 Kč
    Hatchback 332.F12.5 BEV 118k 42 kWh 87kW/118k Elektřina automatická 799 900 Kč 719 900 Kč
    QuboL Maxi (7 míst) 360.CPH.5 1.2 Turbo 110k 81kW/110k Benzín 6st. manuální 659 900 Kč ...

optional body (500's Hatchback/3+1/Cabrio, Qubo L's 5- or 7-seat
length), code, engine, power "kW/hp", fuel, gearbox, then "Ceníková cena"
(the list price) and, on most documents, "Akční cena" (promotional) -
`price` is the first, the same convention as every other brand here.

`model` comes from the page's own title ("FIAT 600E", "FIAT GRANDE PANDA
ELECTRIC", "FIAT 500 HYBRID"). An electric twin keeps its nameplate -
"600e" -> "600", "Grande Panda Electric" -> "Grande Panda", "500e" ->
"500" - the same convention as Opel's "Corsa Electric" -> "Corsa"; the
powertrain tells them apart. Qubo L's long 7-seat body is reported as
"Qubo L Maxi" (Fiat's own name for it, the same split as Citroën's
Berlingo XL).

Powertrain from the row: "BEV"/"Electric" -> EV; "Hybrid" (Stellantis's
48V "1.2 Turbo Hybrid" and Fiat's "1.0 BSG Hybrid" belt-starter mild
hybrid) -> MHEV; otherwise ICE (petrol "Turbo", diesel "MultiJet" /
"BlueHDI"). The fuel word ("Benzín"/"Diesel") is kept in `variant_name`
so the backend import can tell diesel from petrol. The effective date
("Ceník platí od 1.10. do 31.10. 2026") is a monthly window, not
`_pdf_layout.extract_release_date`'s shape, so `release_date` stays None.
Equipment isn't extracted."""

from __future__ import annotations

import re
from pathlib import Path

import pdfplumber

from ._pdf_layout import group_into_lines, line_text
from .base import BaseParser, ExtractedVariant

_TITLE_RE = re.compile(r"^FIAT\s+(?P<title>.+?)\s+Foto je pouze ilustrativní")
# Longest first; maps an upper-cased title to the nameplate.
_TITLE_MODELS = (
    ("GRANDE PANDA", "Grande Panda"),
    ("TIPO", "Tipo Sedan"),
    ("QUBO", "Qubo L"),
    ("PANDINA", "Pandina"),
    ("600", "600"),
    ("500", "500"),
)
_ROW_RE = re.compile(
    r"^(?P<body>.*?)\s*(?P<code>\d{3}\.[A-Z0-9]{3}\.\d\S*)\s+(?P<engine>.+?)\s+"
    r"(?P<kw>\d+)kW/(?P<hp>\d+)k\s+(?P<fuel>Benzín|Diesel|Elektřina)\s+(?P<transmission>.+?)\s+"
    r"(?P<price>\d{1,3}(?: \d{3})+)\s*Kč"
)
_HEADER_WORDS = {"KÓD", "MOTORIZACE"}


def _model_for(title: str) -> str:
    upper = title.upper()
    for prefix, model in _TITLE_MODELS:
        if prefix in upper:
            return model
    return "unknown"


def _classify_powertrain(engine: str) -> str:
    lowered = engine.lower()
    if "bev" in lowered or "electric" in lowered:
        return "EV"
    if "hybrid" in lowered:
        return "MHEV"
    return "ICE"


class FiatParser(BaseParser):
    brand = "fiat"
    powertrain = "ICE"  # nominal default; the actual powertrain is per-row, see _classify_powertrain

    def parse(self, pdf_path: Path) -> list[ExtractedVariant]:
        """See module docstring for the row shape.

        Args:
            pdf_path: Local path to a downloaded Fiat price-list PDF.

        Returns:
            One `ExtractedVariant` per priced row of the "CENÍKOVÉ CENY"
            table.
        """
        variants: list[ExtractedVariant] = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                variants.extend(self._parse_page(page))
        return variants

    @staticmethod
    def _parse_page(page: pdfplumber.page.Page) -> list[ExtractedVariant]:
        """Args:
            page: One page of the price list.

        Returns:
            The page's variants - `[]` for a page without the price table.
        """
        lines = [line_text(line) for line in group_into_lines(page.extract_words())]
        title = next((m.group("title") for m in map(_TITLE_RE.match, lines) if m), None)
        if title is None or not any(_HEADER_WORDS <= set(text.split()) for text in lines):
            return []
        base_model = _model_for(title)

        variants: list[ExtractedVariant] = []
        trim: str | None = None
        in_table = False
        for text in lines:
            if _HEADER_WORDS <= set(text.split()):
                in_table = True
                continue
            if not in_table:
                continue
            match = _ROW_RE.match(text)
            if match is None:
                # A trim heading is a short line of its own with no digits;
                # anything else (footnotes, offers below the table) ends it.
                if text and not any(ch.isdigit() for ch in text) and len(text.split()) <= 3:
                    trim = text.strip()
                    continue
                if trim is not None and variants:
                    break
                continue

            body = match.group("body").strip()
            model = base_model
            if base_model == "Qubo L" and "Maxi" in body:
                model = "Qubo L Maxi"
                body = ""
            elif base_model == "Qubo L":
                body = ""
            engine = match.group("engine").strip()
            spec = " ".join(
                part
                for part in (
                    body,
                    engine,
                    f"{match.group('kw')} kW",
                    match.group("fuel"),
                    match.group("transmission"),
                )
                if part
            )
            variants.append(
                ExtractedVariant(
                    model=model,
                    trim=trim,
                    variant_name=f"{model} {trim or ''} {spec}".replace("  ", " ").strip(),
                    price=float(match.group("price").replace(" ", "")),
                    currency="CZK",
                    source_page=page.page_number,
                    raw_text=f"{trim} | {text}" if trim else text,
                    powertrain=_classify_powertrain(engine),
                )
            )
        return variants
