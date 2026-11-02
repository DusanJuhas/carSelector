"""Parser for Volvo's per-model "Ceník" price lists (verified against all
ten real PDFs downloaded 2026-11-02 from volvodirect.cz, effective 1 Feb-
15 Sep 2026 depending on model, all for model year MY27 - see
scraper/tests/fixtures/volvo_*.pdf). Covers EX30, EX40, EC40, EX60, EX90,
ES90, XC40, XC60, XC90 and V60.

Unlike CUPRA's/Kia's one-row-per-engine list, Volvo's price table is a
genuine trim x engine MATRIX (closer to Ford's own): one column per
engine ("P5 electric", "T8 AWD Long Range", ...), one row per trim
("ULTRA", "PLUS Bright", "CORE", ...), and "-" where that combination
isn't offered. Every document uses the same template, on one page per
powertrain (XC60 has two: a Plug-in Hybrid table on page 3 and a Mild
Hybrid one on page 19 - each read the same way):

    MOTOROVÉ VARIANTY
    Motor                 P3 electric   P5 electric   P8 AWD electric
    Výkon (kW/k)          110/150       200/272       315/429
    ...
    ULTRA
    BLACK EDITION   G5    -             -             1 275 600 Kč
    CORE            A5    -             895 000 Kč    -
    Varianta Kód          416-G8xx-...  416-EMxx-...  416-EKxx-...

Columns are anchored on the bottom "Varianta" row's own per-column
factory codes (`_VARIANT_CODE_RE`, e.g. "416-G8xx-0L1-19") - the one row
that always has exactly one single-word token per engine column (engine
names wrap across 1-3 lines, prices are split into 3-4 words, and the
"Kód" header word is missing on some documents: EC40/EX40/V60/XC40/XC90
print just "Varianta"). Every other token is assigned to the column whose
code's centre is nearest its own centre.

Two things wrap vertically and are reassembled by position, not by line
order (`page.extract_text()` interleaves them with the price rows):

- A trim label like "ULTRA" / "BLACK EDITION" or "PLUS Bright" /
  "(světlý motiv)" is printed as 2-3 lines vertically CENTRED on its own
  price row (±~4pt, verified against word coordinates on every fixture),
  while price rows themselves are ~20pt apart - so each label word is
  assigned to the nearest price row (`_assign_labels`). Parentheticals
  ("(světlý motiv)", "(tmavé provedení)" - a description of the Bright/
  Dark theme, worded differently per document) and "¹" footnote marks are
  dropped, and "BLACK EDITION" vs. "Black Edition" (both spellings occur)
  is normalized to the latter, so the same trim reads the same across
  models: "ULTRA Black Edition", "PLUS Bright", "CORE".
- An engine column header like "P5 LONG RANGE" / "electric" (EX30) or
  "TWIN MOTOR" / "Performance" (EX90/ES90) wraps above and below the
  "Motor" label's own line - every column-region word within
  `_HEADER_BAND` of that line is part of the header. The powertrain
  sub-heading above it ("Elektrický", "zážehový Plug-in Hybrid") sits
  ~20pt higher, outside that band.

`variant_name` appends the "Výkon (kW/k)" row's power as "<N> kW" when
it's a single figure (every EV, e.g. "EX30 PLUS P5 electric 200 kW") so
the backend import can read it; hybrids print a per-motor breakdown
("132+130 / 180+177") with no combined figure, so theirs is left out
rather than picking one motor's number.

Each row also carries a 2-character trim code ("G5", "3M", "65") in its
own narrow column between the label and the first engine - kept in
`raw_text` for verification, not in `trim`.

Powertrain is per table (= per page), from the page's own sub-heading:
"Plug-in Hybrid" -> PHEV, "Mild Hybrid" -> MHEV (Volvo's B3/B4/B5 48V
engines), "Elektrický" -> EV. Volvo sells no plain-ICE car in CZ any more;
anything unrecognized falls back to ICE.

The cover page is just "Ceník Volvo <MODEL>"; the effective date is on
page 3 as "CENÍK platný od D. M. RRRR", not the cover's "Platnost od ..."
that `_pdf_layout.extract_release_date` reads - so `release_date` stays
None and VariantRepository falls back to the download date, same as most
brands here. Standard equipment (Volvo's "STANDARDNÍ VÝBAVA" pages, per
trim, as "<TRIM> (zahrnuje <LOWER TRIM>)" sections) isn't extracted yet."""

from __future__ import annotations

import re
from pathlib import Path

import pdfplumber

from .base import BaseParser, ExtractedVariant

_VARIANT_CODE_RE = re.compile(r"^\d{3}-[A-Za-z0-9]{4}-[A-Za-z0-9]{3}-\d{2}$")
_TRIM_CODE_RE = re.compile(r"^[A-Z0-9]{2}$")
_MODEL_RE = re.compile(r"Ceník Volvo (\S+)")
_PRICE_RE = re.compile(r"^[\d\s]+$")
_SINGLE_POWER_RE = re.compile(r"^(\d+)/\d+$")
_ROW_TOLERANCE = 1.5  # pt; tokens of one price row share `top` within this (labels sit ~4pt off it)
_HEADER_BAND = 9.0  # pt; engine-header lines wrap within this of the "Motor" label's own line
_LABEL_WINDOW = 10.0  # pt; a label's first line can sit this far above the first price row
_FOOTNOTE_MARKS = "¹²³*"


def _group_rows(words: list[dict]) -> list[list[dict]]:
    """Args:
        words: Words of one page.

    Returns:
        Words grouped into rows sharing (within `_ROW_TOLERANCE`) the same
        `top`, top to bottom, each sorted left to right. Deliberately much
        tighter than `_pdf_layout.group_into_lines`' 4pt, which would merge
        a wrapped trim label's own lines into its price row.
    """
    rows: list[list[dict]] = []
    for word in sorted(words, key=lambda w: (w["top"], w["x0"])):
        if rows and abs(rows[-1][0]["top"] - word["top"]) <= _ROW_TOLERANCE:
            rows[-1].append(word)
        else:
            rows.append([word])
    for row in rows:
        row.sort(key=lambda w: w["x0"])
    return rows


def _row_text(row: list[dict]) -> str:
    return " ".join(w["text"] for w in row)


def _center(word: dict) -> float:
    return (word["x0"] + word["x1"]) / 2


def _nearest_column(word: dict, centers: list[float]) -> int:
    return min(range(len(centers)), key=lambda i: abs(centers[i] - _center(word)))


def _clean_label(words: list[str]) -> str:
    """Args:
        words: A trim label's words in reading order, e.g. ["ULTRA",
            "BLACK", "EDITION", "¹"] or ["PLUS", "Bright", "(světlý",
            "motiv)"].

    Returns:
        The normalized trim name ("ULTRA Black Edition", "PLUS Bright") -
        see module docstring.
    """
    text = re.sub(r"\([^)]*\)", " ", " ".join(words))
    tokens = [t.strip(_FOOTNOTE_MARKS) for t in text.split()]
    tokens = [t for t in tokens if t]
    return " ".join([tokens[0], *(t.capitalize() if t.isupper() else t for t in tokens[1:])]) if tokens else ""


def _classify_powertrain(page_text: str) -> str:
    if "Plug-in Hybrid" in page_text:
        return "PHEV"
    if "Mild Hybrid" in page_text:
        return "MHEV"
    if "Elektrický" in page_text:
        return "EV"
    return "ICE"


def _extract_model_name(pdf: pdfplumber.PDF) -> str:
    """Args:
        pdf: The opened price-list PDF.

    Returns:
        The model from the cover page's own "Ceník Volvo <MODEL>" line
        (e.g. "XC60", "EX30"), or "unknown" if it isn't there.
    """
    match = _MODEL_RE.search(pdf.pages[0].extract_text() or "")
    return match.group(1) if match else "unknown"


class VolvoParser(BaseParser):
    brand = "volvo"
    powertrain = "EV"  # nominal default; the actual powertrain is per-table, see _classify_powertrain

    def parse(self, pdf_path: Path) -> list[ExtractedVariant]:
        """See module docstring for the matrix layout and how wrapped
        labels/headers are reassembled.

        Args:
            pdf_path: Local path to a downloaded Volvo price-list PDF.

        Returns:
            One `ExtractedVariant` per priced trim x engine cell, across
            every price-matrix page in the document ("-" cells skipped).
        """
        variants: list[ExtractedVariant] = []
        with pdfplumber.open(pdf_path) as pdf:
            model = _extract_model_name(pdf)
            for page in pdf.pages:
                variants.extend(self._parse_page(page, model))
        return variants

    def _parse_page(self, page: pdfplumber.page.Page, model: str) -> list[ExtractedVariant]:
        """Args:
            page: One page of the price list.
            model: This document's model name.

        Returns:
            The page's variants, or `[]` if it has no price matrix (no
            "Motor" header row plus "Varianta" code row).
        """
        rows = _group_rows(page.extract_words())
        code_row = next((r for r in rows if r[0]["text"] == "Varianta"), None)
        motor_row = next((r for r in rows if r[0]["text"] == "Motor"), None)
        if code_row is None or motor_row is None:
            return []
        codes = [w for w in code_row if _VARIANT_CODE_RE.match(w["text"])]
        if not codes:
            return []

        centers = [_center(w) for w in codes]
        column_left = min(w["x0"] for w in codes) - 15
        code_top = code_row[0]["top"]
        motor_top = motor_row[0]["top"]

        engines = self._engine_names(rows, motor_top, column_left, centers)
        powers = self._power_kw(rows, column_left, centers)
        price_rows = [
            r
            for r in rows
            if motor_top < r[0]["top"] < code_top
            and any(w["x0"] >= column_left and w["text"] in ("Kč", "-") for w in r)
        ]
        if not price_rows:
            return []
        labels = self._assign_labels(rows, price_rows, column_left, code_top)
        powertrain = _classify_powertrain(page.extract_text() or "")

        variants: list[ExtractedVariant] = []
        for index, row in enumerate(price_rows):
            label_words = labels[index]
            trim = _clean_label([w["text"] for w in label_words])
            cells: list[list[str]] = [[] for _ in centers]
            for word in row:
                if word["x0"] >= column_left:
                    cells[_nearest_column(word, centers)].append(word["text"])

            label_text = _row_text(sorted(label_words, key=lambda w: (w["top"], w["x0"])))
            for column, cell in enumerate(cells):
                if not cell or cell[-1] != "Kč":
                    continue  # "-" (not offered) or an empty cell
                amount = " ".join(cell[:-1])
                if not _PRICE_RE.match(amount):
                    continue
                engine = engines[column]
                spec = f"{engine} {powers[column]} kW" if powers[column] else engine
                variants.append(
                    ExtractedVariant(
                        model=model,
                        trim=trim,
                        variant_name=f"{model} {trim} {spec}".strip(),
                        price=float(amount.replace(" ", "")),
                        currency="CZK",
                        source_page=page.page_number,
                        raw_text=" | ".join([label_text, engine, _row_text(row)]),
                        powertrain=powertrain,
                    )
                )
        return variants

    @staticmethod
    def _engine_names(rows: list[list[dict]], motor_top: float, column_left: float, centers: list[float]) -> list[str]:
        """Args:
            rows: The page's rows (`_group_rows`).
            motor_top: `top` of the row starting with the "Motor" label.
            column_left: Left edge of the first engine column.
            centers: Each engine column's centre x.

        Returns:
            One engine name per column, its wrapped header lines joined
            top to bottom (e.g. "P5 LONG RANGE electric"), footnote marks
            stripped.
        """
        parts: list[list[str]] = [[] for _ in centers]
        for row in rows:
            if abs(row[0]["top"] - motor_top) > _HEADER_BAND:
                continue
            for word in row:
                if word["x0"] >= column_left:
                    text = word["text"].strip(_FOOTNOTE_MARKS)
                    if text:
                        parts[_nearest_column(word, centers)].append(text)
        return [" ".join(p) for p in parts]

    @staticmethod
    def _power_kw(rows: list[list[dict]], column_left: float, centers: list[float]) -> list[str | None]:
        """Args:
            rows: The page's rows (`_group_rows`).
            column_left: Left edge of the first engine column.
            centers: Each engine column's centre x.

        Returns:
            Each column's power in kW from the "Výkon (kW/k)" row, when it
            is a single "kW/k" figure ("200/272" -> "200"). `None` for a
            hybrid's per-motor breakdown ("132+130 / 180+177" - Volvo's
            table has no combined figure) or a missing row.
        """
        powers: list[str | None] = [None for _ in centers]
        row = next((r for r in rows if r[0]["text"] == "Výkon"), None)
        if row is None:
            return powers
        cells: list[list[str]] = [[] for _ in centers]
        for word in row:
            if word["x0"] >= column_left:
                cells[_nearest_column(word, centers)].append(word["text"])
        for column, cell in enumerate(cells):
            match = _SINGLE_POWER_RE.match(" ".join(cell))
            if match:
                powers[column] = match.group(1)
        return powers

    @staticmethod
    def _assign_labels(
        rows: list[list[dict]], price_rows: list[list[dict]], column_left: float, code_top: float
    ) -> list[list[dict]]:
        """Args:
            rows: The page's rows (`_group_rows`).
            price_rows: The subset of `rows` that carry prices.
            column_left: Left edge of the first engine column.
            code_top: `top` of the bottom "Varianta" row (end of table).

        Returns:
            For each price row (same order), the trim-label words assigned
            to it: every label-region word between the table's first
            price row (minus `_LABEL_WINDOW`) and the "Varianta" row,
            attached to the vertically nearest price row - see module
            docstring. The 2-character trim-code column is excluded.
        """
        first_top = price_rows[0][0]["top"]
        row_tops = [r[0]["top"] for r in price_rows]
        trim_code_x0 = min(
            (w["x0"] for r in price_rows for w in r if w["x0"] < column_left and _TRIM_CODE_RE.match(w["text"])),
            default=column_left,
        )
        assigned: list[list[dict]] = [[] for _ in price_rows]
        for row in rows:
            if not first_top - _LABEL_WINDOW <= row[0]["top"] < code_top:
                continue
            for word in row:
                if word["x1"] > trim_code_x0 - 2:
                    continue
                nearest = min(range(len(row_tops)), key=lambda i: abs(row_tops[i] - word["top"]))
                assigned[nearest].append(word)
        return assigned
