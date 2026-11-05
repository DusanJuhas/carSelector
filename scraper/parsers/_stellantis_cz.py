"""Shared row parser for the Stellantis Czech importer's (F Automobil
Import s.r.o.) per-model price lists - the same "CENÍKOVÉ (A AKČNÍ) CENY"
page layout is used by Jeep and Alfa Romeo (see `parsers/jeep.py`,
`parsers/alfa_romeo.py`); Fiat prints the same table without the drive
column and predates this module (`parsers/fiat.py`).

The price page carries a title line, a column header, then trim headings
each followed by one row per variant, anchored on Stellantis's own order
code:

    NOVÝ JEEP AVENGER Foto je pouze ilustrativní.
    KÓD MOTORIZACE VÝKON PALIVO PŘEVODOVKA HNACÍ NÁPRAVA CENÍKOVÁ CENA AKČNÍ CENA
    LONGITUDE
    619.M29.4 1.2 Turbo 100k 74kW/100k Benzín 6st. manuální Přední 539 900 Kč 449 900 Kč
    85TH ANNIVERSARY
    619.849.4 1.2 Turbo 100k 74kW/100k Benzín 6st. manuální Přední 679 900 Kč 569 900 Kč

code, engine, power "kW/hp", fuel, gearbox, drive, then "Ceníková cena"
(the list price) and, where printed, "Akční cena" (promotional) - `price`
is the first, the same convention as every other brand here. The fuel
and drive words are kept in `variant_name`, because the backend import
reads diesel ("Diesel") and AWD/RWD ("4WD", "eAWD", "Q4 (AWD)", "Pohon
všech kol", "Zadní (RWD)") from there.

A trim heading is any short non-row line inside the table ("SUMMIT",
"Veloce 280", "85TH ANNIVERSARY" - digits allowed, unlike Fiat's own
headings); all-caps headings are re-cased ("Sport Speciale", "85th
Anniversary"). Lines after the table (offers, footnotes) can update the
pending heading but never precede another row, so they're harmless.

Powertrain from the row: an "Electric"/"Elettrica" engine or "Elektřina"
fuel -> EV; a two-part fuel ("Benzín/Elektřina", "benzín/PHEV") or a
"Plug-in"/"PHEV" engine -> PHEV; otherwise "Hybrid" (Stellantis's 48V
"e-Hybrid"/"Turbo Hybrid", incl. Avenger's "e-Hybrid 4xe") -> MHEV;
otherwise ICE. The effective date ("Ceník platí od 1.11. do 30.11.2026")
is a monthly window, not `_pdf_layout.extract_release_date`'s shape, so
`release_date` stays None. Equipment isn't extracted."""

from __future__ import annotations

import re
from pathlib import Path

import pdfplumber

from ._pdf_layout import group_into_lines, line_text
from .base import BaseParser, ExtractedVariant

_ROW_RE = re.compile(
    r"^(?P<code>\d{3}\.[A-Z0-9]{3}\.\d\S*)\s+(?P<engine>.+?)\s+(?P<kw>\d+)kW/(?P<hp>\d+)k\s+"
    r"(?P<fuel>\S+)\s+(?P<transmission>(?:\d+st\.\s+)?(?:automatická|manuální))\s+(?P<drive>.+?)\s+"
    r"(?P<price>\d{1,3}(?: \d{3})+)\s*Kč"
)
_HEADER_WORDS = {"KÓD", "MOTORIZACE"}
_MAX_HEADING_WORDS = 4


def classify_powertrain(engine: str, fuel: str) -> str:
    """Args:
        engine: The row's MOTORIZACE text, e.g. "1.2 Turbo e-Hybrid 110k".
        fuel: The row's PALIVO token, e.g. "Benzín", "benzín/PHEV".

    Returns:
        "EV", "PHEV", "MHEV" or "ICE", by the rules in the module docstring.
    """
    engine_lower, fuel_lower = engine.lower(), fuel.lower()
    if "electric" in engine_lower or "elettrica" in engine_lower or fuel_lower == "elektřina":
        return "EV"
    if "/" in fuel_lower or "plug-in" in engine_lower or "phev" in engine_lower:
        return "PHEV"
    if "hybrid" in engine_lower:
        return "MHEV"
    return "ICE"


def normalize_heading(text: str) -> str:
    """Args:
        text: A trim heading as printed, e.g. "SPORT SPECIALE", "Luna Rossa".

    Returns:
        All-caps headings re-cased word by word ("Sport Speciale", "85th
        Anniversary"); mixed-case headings unchanged.
    """
    text = " ".join(text.split())
    if text != text.upper():
        return text
    return " ".join(word[:1] + word[1:].lower() for word in text.split())


class StellantisCzParser(BaseParser):
    """Base for one Stellantis CZ brand. Subclasses set `brand`,
    `_title_re` (whose `title` group is the page title without the brand
    prefix) and `_title_models` (upper-case title substring -> model,
    longest/most specific first)."""

    powertrain = "ICE"  # nominal default; the actual powertrain is per-row, see classify_powertrain
    _title_re: re.Pattern[str]
    _title_models: tuple[tuple[str, str], ...]

    def parse(self, pdf_path: Path) -> list[ExtractedVariant]:
        """See module docstring for the row shape.

        Args:
            pdf_path: Local path to a downloaded price-list PDF.

        Returns:
            One `ExtractedVariant` per priced row of the "CENÍKOVÉ CENY"
            table.
        """
        variants: list[ExtractedVariant] = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                variants.extend(self._parse_page(page))
        return variants

    def model_for(self, title: str) -> str | None:
        """Args:
            title: The price page's title without the brand prefix, e.g.
                "AVENGER ELECTRIC", "GIULIA QUADRIFOGLIO".

        Returns:
            The model nameplate, or `None` for a title no rule covers.
        """
        upper = title.upper()
        for needle, model in self._title_models:
            if needle in upper:
                return model
        return None

    def _parse_page(self, page: pdfplumber.page.Page) -> list[ExtractedVariant]:
        """Args:
            page: One page of the price list.

        Returns:
            The page's variants - `[]` for a page without the price table
            or with a title `model_for` doesn't recognise.
        """
        lines = [line_text(line) for line in group_into_lines(page.extract_words())]
        title = next((m.group("title") for m in map(self._title_re.match, lines) if m), None)
        if title is None or not any(_HEADER_WORDS <= set(text.split()) for text in lines):
            return []
        model = self.model_for(title)
        if model is None:
            return []

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
                if text and "Kč" not in text and not text.startswith("*") and len(text.split()) <= _MAX_HEADING_WORDS:
                    trim = normalize_heading(text)
                continue
            variants.append(self._variant(model, trim, match, text, page.page_number))
        return variants

    def _variant(
        self, model: str, trim: str | None, match: re.Match[str], text: str, page_number: int
    ) -> ExtractedVariant:
        """Args:
            model: The page's model nameplate.
            trim: The current trim heading, or `None` before any heading.
            match: `_ROW_RE`'s match on the row.
            text: The row as printed.
            page_number: 1-based page the row is on.

        Returns:
            The row's variant.
        """
        engine = " ".join(match.group("engine").split())
        # Don't print the trim twice: a trim named like the model (Alfa's
        # base "Junior"/"Tonale") or already leading the engine text
        # ("Veloce 280 Elettrica 54 kWh") is left out of the name.
        named_trim = trim if trim and trim != model and not engine.startswith(trim) else None
        spec = " ".join(
            (
                engine,
                f"{match.group('kw')} kW",
                match.group("fuel"),
                match.group("transmission"),
                " ".join(match.group("drive").split()),
            )
        )
        return ExtractedVariant(
            model=model,
            trim=trim,
            variant_name=" ".join(part for part in (model, named_trim, spec) if part),
            price=float(match.group("price").replace(" ", "")),
            currency="CZK",
            source_page=page_number,
            raw_text=f"{trim} | {text}" if trim else text,
            powertrain=classify_powertrain(engine, match.group("fuel")),
        )
