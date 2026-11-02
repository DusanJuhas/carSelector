"""Parser for Lexus's per-model "Oficiální ceník" price lists (verified
against all ten real PDFs downloaded 2026-11-02 from content.lexus-ce.com,
model years 2026-2027 - see scraper/tests/fixtures/lexus_*.pdf). Covers
LBX, UX, NX (350h and 450h+ documents), ES, RX (350h, 450h+, 500h
documents), RZ and LM.

Every document has one price page - page 2, "CENY" (LM's: "CENÍKOVÉ
CENY") - laid out as a trim x engine MATRIX, Volvo-like:

    300h FWD  SFX  300h AWD  SFX  350e FWD  SFX  500e AWD  SFX
    PRESTIGE      1 690 000 KČ AA  1 770 000 KČ 0A  1 860 000 KČ KA  1 960 000 KČ A0
    PRESTIGE TOP  1 790 000 KČ GA  1 870 000 KČ JA  —  —  —  —

one row per trim, one column per engine (or, for LM, per seat count:
"7 MÍST" / "4 MÍSTA"), "—"/"–"/"-" where not offered. Most documents
interleave an "SFX" order-code column after each engine (ES, RZ) or put
one at the end (NX, RX, UX, LBX); SFX codes can be all-digit ("15",
"06"), so a price cell is read as a run of digit words ENDED by "KČ"/
"Kč" - an SFX code never is - and assigned to the engine column whose
header is horizontally nearest (`_nearest`). Header words are grouped
into column labels by gap; "SFX" and the trim column's own header (LM's
"ZÁKLADNÍ VERZE") are dropped.

`model` is the family ("NX", "RX", ...), found in the cover page's own
"NX 350h" / "ES 300h | ES 350e | ES 500e" line - or, for LBX, whose cover
has no text at all, the first page that names it (its colour table).
Where a column header has no engine code of its own (LBX's "FWD" /
"4X4 E-FOUR", LM's seat counts), the cover's engine code is prefixed when
there is one (LM: "350h 7 MÍST"). Powertrain comes from the engine code:
"450h+" -> PHEV, "350e"/"500e" -> EV, otherwise (a plain "h" code, or
LBX with none - its only drivetrain is a full hybrid) -> HEV.

The model-year line ("OFICIÁLNÍ CENÍK | MODELOVÝ ROK 2026") has no
effective date, so `release_date` stays None. The promotional pages that
follow ("ZVÝHODNĚNÁ NABÍDKA": STANDARDNÍ CENA / ZVÝHODNĚNÍ / AKČNÍ CENA
for a few trims) and the equipment pages aren't read - only the regular
price matrix."""

from __future__ import annotations

import re
from pathlib import Path

import pdfplumber

from .base import BaseParser, ExtractedVariant

_FAMILIES = ("LBX", "UX", "NX", "RX", "RZ", "ES", "LM")
_FAMILY_RE = re.compile(r"\b(" + "|".join(_FAMILIES) + r")\b(?:\s+(\d{3}[a-z]\+?))?")
_ENGINE_CODE_RE = re.compile(r"\b\d{3}[a-z]\+?")
_CURRENCY = {"KČ", "Kč"}
_ROW_TOLERANCE = 1.5  # pt; a row's SFX code sits ~0.2pt off its prices
_LABEL_GAP = 12.0  # pt; wider than a word space, narrower than the gap between column labels


def _group_rows(words: list[dict]) -> list[list[dict]]:
    rows: list[list[dict]] = []
    for word in sorted(words, key=lambda w: (w["top"], w["x0"])):
        if rows and abs(rows[-1][0]["top"] - word["top"]) <= _ROW_TOLERANCE:
            rows[-1].append(word)
        else:
            rows.append([word])
    for row in rows:
        row.sort(key=lambda w: w["x0"])
    return rows


def _price_cells(row: list[dict], left: float) -> list[tuple[float, float]]:
    """Args:
        row: One row's words, left to right.
        left: Only words at or right of this x are price-cell candidates.

    Returns:
        `(centre_x, price)` for every run of digit words ended by
        "KČ"/"Kč" (see module docstring).
    """
    cells: list[tuple[float, float]] = []
    run: list[dict] = []
    for word in row:
        if word["x0"] < left:
            continue
        if word["text"].isdigit():
            run.append(word)
        elif word["text"] in _CURRENCY and run:
            cells.append(((run[0]["x0"] + word["x1"]) / 2, float("".join(w["text"] for w in run))))
            run = []
        else:
            run = []
    return cells


def _column_labels(header: list[dict], left: float) -> list[tuple[float, str]]:
    """Args:
        header: The header row's words, left to right.
        left: Words left of this x belong to the trim column's header.

    Returns:
        `(centre_x, label)` per engine column, "SFX" dropped.
    """
    groups: list[list[dict]] = []
    for word in header:
        if word["x0"] < left or word["text"] == "SFX":
            continue
        if groups and word["x0"] - groups[-1][-1]["x1"] <= _LABEL_GAP:
            groups[-1].append(word)
        else:
            groups.append([word])
    return [((g[0]["x0"] + g[-1]["x1"]) / 2, " ".join(w["text"] for w in g)) for g in groups]


def _nearest(x: float, centers: list[float]) -> int:
    return min(range(len(centers)), key=lambda i: abs(centers[i] - x))


def _classify_powertrain(engine: str) -> str:
    code = _ENGINE_CODE_RE.search(engine)
    if code is None:
        return "HEV"
    if code.group(0).endswith("+"):
        return "PHEV"
    if code.group(0).endswith("e"):
        return "EV"
    return "HEV"


class LexusParser(BaseParser):
    brand = "lexus"
    powertrain = "HEV"  # nominal default; the actual powertrain is per-column, see _classify_powertrain

    def parse(self, pdf_path: Path) -> list[ExtractedVariant]:
        """See module docstring for the matrix layout.

        Args:
            pdf_path: Local path to a downloaded Lexus price-list PDF.

        Returns:
            One `ExtractedVariant` per priced trim x engine cell of the
            price matrix (first page that has one).
        """
        with pdfplumber.open(pdf_path) as pdf:
            family, cover_engine = self._family(pdf)
            for page in pdf.pages[:6]:
                variants = self._parse_page(page, family, cover_engine)
                if variants:
                    return variants
        return []

    @staticmethod
    def _family(pdf: pdfplumber.PDF) -> tuple[str, str | None]:
        """Args:
            pdf: The opened price list.

        Returns:
            `(family, engine_code)` from the first page naming a family
            (cover first) - engine code `None` if not printed next to it.
        """
        for page in pdf.pages[:10]:
            match = _FAMILY_RE.search(page.extract_text() or "")
            if match:
                return match.group(1), match.group(2)
        return "unknown", None

    @staticmethod
    def _parse_page(page: pdfplumber.page.Page, family: str, cover_engine: str | None) -> list[ExtractedVariant]:
        """Args:
            page: One page of the price list.
            family: The model family.
            cover_engine: The cover's engine code, if any.

        Returns:
            The page's variants, or `[]` if it has no price matrix (or is
            a promotional page whose rows have no trim/engine matrix).
        """
        rows = _group_rows(page.extract_words())
        priced = [(index, row) for index, row in enumerate(rows) if _price_cells(row, 0)]
        if not priced or "ZVÝHODNĚNÁ" in (page.extract_text() or ""):
            return []
        left = min(w["x0"] for _i, row in priced for w in row if w["text"].isdigit()) - 30
        header = rows[priced[0][0] - 1] if priced[0][0] > 0 else []
        labels = _column_labels(header, left)
        if not labels:
            return []
        centers = [x for x, _label in labels]

        variants: list[ExtractedVariant] = []
        for _index, row in priced:
            trim = " ".join(w["text"] for w in row if w["x1"] < left)
            if not trim:
                continue
            for x, price in _price_cells(row, left):
                label = labels[_nearest(x, centers)][1]
                engine = label
                if cover_engine and not _ENGINE_CODE_RE.search(label) and family != "LBX":
                    engine = f"{cover_engine} {label}"
                variants.append(
                    ExtractedVariant(
                        model=family,
                        trim=trim,
                        variant_name=f"{family} {trim} {engine}",
                        price=price,
                        currency="CZK",
                        source_page=page.page_number,
                        raw_text=f"{' '.join(w['text'] for w in header)} | {' '.join(w['text'] for w in row)}",
                        powertrain=_classify_powertrain(engine),
                    )
                )
        return variants
