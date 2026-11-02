"""Parser for Citroën's per-model "Ceník" price lists (verified against
real PDFs downloaded 2026-11-02 from data.citroen.cz, valid from
1 October 2026 - see scraper/tests/fixtures/citroen_*.pdf). Covers C3,
C3 Aircross, C4, C4 X, C5 Aircross and Berlingo (whose document holds two
tables, "BERLINGO M" and "BERLINGO XL" - read as "Berlingo" and
"Berlingo XL", the same body-length split as Peugeot's Rifter/Rifter
Long). SpaceTourer's own document is a van-style list (commercial codes,
prices with and without VAT, no trim column) and isn't covered, the same
call PeugeotParser makes for its sister model Traveller.

Every covered document uses one table template, one table per page:

    Úroveň výbavy | Motor                                   | Standardní cena | Akční cena | ...
    YOU           | Turbo 100k Manual                       | 420 000         | 385 000    | ...
                  | Electric 113k Standard range Automatic  | 585 000         | 554 000    | ...
                  | (Baterie 30 kWh)                        |                 |            |

`price` is "Standardní cena" (the list price) - the "Akční cena" columns
after it (promotional, trade-in-bonus, financing or ex-VAT business
prices, 2-3 of them depending on the document) are read then discarded,
the same "list price, not a promotional one" convention as every other
brand here.

Two cells wrap vertically and are reassembled by position, not by the
line order `page.extract_text()` gives (which interleaves them):

- A row is anchored on its line of prices - every row has exactly one,
  starting with a "NNN NNN"-shaped figure in the first price column. An
  electric engine's description wraps above and below that line
  ("Electric 113k Standard range Automatic" / "(Baterie 44 kWh)", ±~5pt,
  rows ~15-25pt apart), so every engine-column word joins the vertically
  nearest price line (`_nearest`).
- The trim ("Úroveň výbavy") cell is MERGED across all of a trim's rows,
  its label printed once, centred. As on Mitsubishi's tables, nearest-
  label is ambiguous for a 3-row group's last row, but the table draws a
  rule across the trim column at each group boundary (verified on every
  table of all six documents; the engine column's own per-row rules are
  NOT reliable - C4's table has almost none), so `_trim_bands` reads those
  and each row takes the label inside its own band, falling back to
  nearest-label only if a page had no usable rules.

The PDF's display font renders trim names in mixed case ("YoU",
"CoLLECTIon", "COLLeCTIOn") - normalized to upper case ("YOU",
"COLLECTION", "30 LET"). Engine footnote marks ("Automatic(2)") are
dropped.

`model` comes from each table page's own title line ("nový citroËn C3",
"citroËn BERLINGO XL") - or, where the table page has no title of its own
(C3 Aircross/C4/C4 X/C5 Aircross put it on the cover page), the cover's -
matched against `_KNOWN_MODELS`.

Powertrain is classified from the engine text: "Plug-in Hybrid" -> PHEV;
"Hybrid" otherwise -> MHEV (Stellantis's 48V mild hybrid - the same
convention as PeugeotParser/OpelParser); "Electric" -> EV; Turbo/Petrol/
Diesel -> ICE. Power is printed in horsepower only ("113k"), so no kW
figure is added to `variant_name`.

The effective date ("Akční ceník s platností od 1. 10. 2026") isn't in
`_pdf_layout.extract_release_date`'s "Platnost od ..." format, so
`release_date` stays None (download date used instead). Equipment pages
aren't extracted yet."""

from __future__ import annotations

import re
from pathlib import Path

import pdfplumber

from .base import BaseParser, ExtractedVariant

# Longest first, so "C3 AIRCROSS" isn't read as "C3" and "BERLINGO XL" as "Berlingo".
_KNOWN_MODELS = ("C3 Aircross", "C5 Aircross", "C4 X", "C3", "C4", "Berlingo XL", "Berlingo")
_TITLE_RE = re.compile(r"^(?:nov\w\s+)?citro[eë]n\s+(.+)$", re.IGNORECASE)
_PRICE_RE = re.compile(r"^\d{1,3}(?: \d{3})+$")
# "(2)", "(*)", and a stray "(í*)" mark C5 Aircross prints under its last row - never "(Baterie 44 kWh)".
_FOOTNOTE_RE = re.compile(r"\(\d\)|\([^)\s]*\*[^)\s]*\)")
_ROW_TOLERANCE = 1.5  # pt; words of one printed line share `top` within this
_CELL_GAP = 8.0  # pt; wider than the space inside "1 019 900", narrower than the gap between price columns
_RULE_MERGE = 1.5  # pt; a drawn rule is often two edges this close together


def _group_lines(words: list[dict]) -> list[list[dict]]:
    """Args:
        words: Words of one page (or a subset of them).

    Returns:
        Words grouped into printed lines (same `top` within
        `_ROW_TOLERANCE`), top to bottom, each sorted left to right.
    """
    lines: list[list[dict]] = []
    for word in sorted(words, key=lambda w: (w["top"], w["x0"])):
        if lines and abs(lines[-1][0]["top"] - word["top"]) <= _ROW_TOLERANCE:
            lines[-1].append(word)
        else:
            lines.append([word])
    for line in lines:
        line.sort(key=lambda w: w["x0"])
    return lines


def _first_cell(words: list[dict]) -> str:
    """Args:
        words: One line's price-region words, left to right.

    Returns:
        The text of the first price column ("1 019 900") - words up to the
        first gap wider than `_CELL_GAP`.
    """
    cell = [words[0]]
    for word in words[1:]:
        if word["x0"] - cell[-1]["x1"] > _CELL_GAP:
            break
        cell.append(word)
    return " ".join(w["text"] for w in cell)


def _nearest(top: float, tops: list[float]) -> int:
    return min(range(len(tops)), key=lambda i: abs(tops[i] - top))


def _normalize_model(title: str) -> str | None:
    """Args:
        title: The model part of a title line, e.g. "C3 AirCrOss",
            "BERLINGO M".

    Returns:
        The canonical model from `_KNOWN_MODELS`, or `None`.
    """
    upper = " ".join(title.upper().split())
    for model in _KNOWN_MODELS:
        if re.search(rf"(?<![\w-]){re.escape(model.upper())}(?![\w-])", upper):
            return model
    return None


def _title_model(page: pdfplumber.page.Page) -> str | None:
    """Args:
        page: A page of the price list.

    Returns:
        The model named by the page's own "[nový] citroën <MODEL>" title
        line, or `None` if it has none.
    """
    for line in (page.extract_text() or "").splitlines():
        match = _TITLE_RE.match(line.strip())
        if match:
            model = _normalize_model(match.group(1))
            if model:
                return model
    return None


def _classify_powertrain(engine: str) -> str:
    lowered = engine.lower()
    if "plug-in" in lowered:
        return "PHEV"
    if "hybrid" in lowered:
        return "MHEV"
    if "electric" in lowered:
        return "EV"
    return "ICE"


def _trim_bands(page: pdfplumber.page.Page, left: float, right: float, top: float) -> list[float]:
    """Args:
        page: The table page.
        left: x0 of the "Úroveň" header word (the trim column's text start).
        right: x0 of the "Motor" header word (the trim column's right edge).
        top: `top` of the "Motor" header word.

    Returns:
        Sorted `top`s of the horizontal rules spanning the trim column
        below the header (near-duplicates merged) - the trim-group
        boundaries, see module docstring.
    """
    tops = sorted(
        e["top"]
        for e in page.edges
        if e["orientation"] == "h" and e["x0"] <= left + 2 and e["x1"] >= right - 5 and e["top"] > top
    )
    bands: list[float] = []
    for value in tops:
        if not bands or value - bands[-1] > _RULE_MERGE:
            bands.append(value)
    return bands


class CitroenParser(BaseParser):
    brand = "citroen"
    powertrain = "ICE"  # nominal default; the actual powertrain is per-row, see _classify_powertrain

    def parse(self, pdf_path: Path) -> list[ExtractedVariant]:
        """See module docstring for the table shape and how wrapped cells
        are reassembled.

        Args:
            pdf_path: Local path to a downloaded Citroën price-list PDF.

        Returns:
            One `ExtractedVariant` per priced trim x engine row, across
            every table page in the document.
        """
        variants: list[ExtractedVariant] = []
        with pdfplumber.open(pdf_path) as pdf:
            cover_model = _title_model(pdf.pages[0])
            for page in pdf.pages:
                model = _title_model(page) or cover_model or "unknown"
                variants.extend(self._parse_page(page, model))
        return variants

    def _parse_page(self, page: pdfplumber.page.Page, model: str) -> list[ExtractedVariant]:
        """Args:
            page: One page of the price list.
            model: The model this page's table belongs to.

        Returns:
            The page's variants, or `[]` if it has no "Úroveň výbavy /
            Motor / Standardní cena" table.
        """
        words = page.extract_words()
        level = next((w for w in words if w["text"] == "Úroveň"), None)
        motor = next((w for w in words if w["text"] == "Motor"), None)
        standard = next((w for w in words if w["text"] == "Standardní"), None)
        if level is None or motor is None or standard is None:
            return []

        header_bottom = max(w["bottom"] for w in words if w["text"] == "(Kč)" or w is motor)
        price_left = standard["x0"] - 12
        body = [w for w in words if w["top"] > header_bottom]

        # The table ends at the first footnote/marketing line below it ("> Prodloužená ...", "(1) ...").
        end = min(
            (w["top"] for w in body if w["x0"] < motor["x0"] and w["text"] in (">", "(1)", "*")),
            default=page.height,
        )
        body = [w for w in body if w["top"] < end]

        price_lines = [
            line
            for line in _group_lines([w for w in body if w["x0"] >= price_left])
            if _PRICE_RE.match(_first_cell(line))
        ]
        if not price_lines:
            return []
        row_tops = [line[0]["top"] for line in price_lines]

        engine_words: list[list[dict]] = [[] for _ in price_lines]
        for word in body:
            if motor["x0"] - 2 <= word["x0"] and word["x1"] < price_left + 5:
                engine_words[_nearest(word["top"], row_tops)].append(word)

        labels = [w for w in body if w["x1"] < motor["x0"] - 2]
        bands = _trim_bands(page, level["x0"], motor["x0"], motor["top"])

        variants: list[ExtractedVariant] = []
        for index, line in enumerate(price_lines):
            engine_line = sorted(engine_words[index], key=lambda w: (round(w["top"]), w["x0"]))
            engine = " ".join(_FOOTNOTE_RE.sub("", " ".join(w["text"] for w in engine_line)).split())
            if not engine:
                continue
            trim = self._trim_for_row(row_tops[index], bands, labels)
            price_text = _first_cell(line)
            raw = " ".join(w["text"] for w in line)
            variants.append(
                ExtractedVariant(
                    model=model,
                    trim=trim,
                    variant_name=f"{model} {trim or ''} {engine}".replace("  ", " ").strip(),
                    price=float(price_text.replace(" ", "")),
                    currency="CZK",
                    source_page=page.page_number,
                    raw_text=" | ".join(part for part in (trim, engine, raw) if part),
                    powertrain=_classify_powertrain(engine),
                )
            )
        return variants

    @staticmethod
    def _trim_for_row(row_top: float, bands: list[float], labels: list[dict]) -> str | None:
        """Args:
            row_top: `top` of the row's price line.
            bands: Trim-group boundaries from `_trim_bands`.
            labels: Every trim-column word in the table body.

        Returns:
            The upper-cased label inside the band containing `row_top`, or
            - with no usable rules - the vertically nearest label line;
            `None` if there's no label at all.
        """
        upper = next((b for b in bands if b > row_top), None)
        lower = max((b for b in bands if b <= row_top), default=None)
        inside = [w for w in labels if lower <= w["top"] < upper] if upper is not None and lower is not None else []
        if not inside and labels:
            nearest_top = labels[_nearest(row_top, [w["top"] for w in labels])]["top"]
            inside = [w for w in labels if abs(w["top"] - nearest_top) <= _ROW_TOLERANCE]
        if not inside:
            return None
        ordered = sorted(inside, key=lambda w: (round(w["top"]), w["x0"]))
        return " ".join(w["text"] for w in ordered).upper()
