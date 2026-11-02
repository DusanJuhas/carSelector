"""Parser for Subaru's per-model "Ceník" price lists (verified against all
five real PDFs downloaded 2026-11-02 from subaru.cz, valid from 1 September
or 1 October 2026 - see scraper/tests/fixtures/subaru_*.pdf). Covers
Impreza and Forester (petrol e-Boxer hybrids) and the electric Solterra,
Uncharted and e-Outback. Subaru's Crosstrek and Outback pages currently
link no price list at all, so they aren't covered.

`model` is the cover's own "SUBARU <NAME>" title. The two drivetrain
families use two different table shapes:

**Impreza / Forester** - one row per trim (page 1):

    SPECIFIKACE  BOXER            PŘEVODOVKA  ...  CENA KČ BEZ DPH  CENA KČ VČ. 21% DPH  AKČNÍ CENA VČ. BONUSU
                 FB20                              ...
    ACTIVE                        CVT         ...  847 107          1 025 000            985 000
                 100 kW (136 k)

The three prices (ex-VAT, incl. VAT, promotional) are printed with
spaces both inside and between them ("847 107 1 025 000 985 000"), so
they're told apart by position: every price word goes to the nearest of
the three price-column headers, and `price` is the incl.-VAT list
column. The engine cell wraps above and below the row ("FB20" /
"100 kW (136 k)", Impreza "e-Boxer FB20") and is collected from the BOXER
column within `_WRAP` of the row. Both are e-Boxer (mild) hybrids -
classified MHEV.

**Solterra / Uncharted / e-Outback** - transposed (page 2): trims are
columns (LIMITED, COMFORT, EXECUTIVE, TOURING), one row per battery/drive
spec ("77 AWD", "AWD 73"), each with a list-price line ("1 190 000 Kč")
and a promotional one just below it ("1 150 000 Kč*", with an asterisk),
"-" where a trim isn't offered. A price cell is a run of digit words
ended by exactly "Kč" - the promotional "Kč*" never matches - assigned to
the nearest trim column. The spec's detail line ("kapacita akumulátoru
74.7kWh, pohon AWD, výkon 280 kW/375 HP, ...") adds the power in kW when
it states one (e-Outback); Solterra/Uncharted give horsepower only.

Every document's effective date is a validity window ("PLATNÝ OD
1.10.2026 DO 31.12.2026", "platný od 1. 9. 2026 do 1. 12. 2026"), which
`_pdf_layout.extract_release_date` doesn't read, so `release_date` stays
None. The equipment tables aren't extracted."""

from __future__ import annotations

import re
from pathlib import Path

import pdfplumber

from .base import BaseParser, ExtractedVariant

_TITLE_RE = re.compile(r"SUBARU\s+(E-OUTBACK|SOLTERRA|UNCHARTED|FORESTER|IMPREZA|CROSSTREK|OUTBACK)\b", re.IGNORECASE)
_MODEL_NAMES = {
    "E-OUTBACK": "e-Outback",
    "SOLTERRA": "Solterra",
    "UNCHARTED": "Uncharted",
    "FORESTER": "Forester",
    "IMPREZA": "Impreza",
    "CROSSTREK": "Crosstrek",
    "OUTBACK": "Outback",
}
_KW_RE = re.compile(r"(\d+)\s*kW\b")
_SPEC_LABEL_RE = re.compile(r"^(?:\d+\s+(?:FWD|AWD)|(?:FWD|AWD)\s+\d+)$")
_ROW_TOLERANCE = 1.5  # pt
_WRAP = 6.0  # pt; wrapped engine-cell lines sit ~4pt above/below their row


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


def _center(words: list[dict]) -> float:
    return (words[0]["x0"] + words[-1]["x1"]) / 2


def _nearest(x: float, centers: list[float]) -> int:
    return min(range(len(centers)), key=lambda i: abs(centers[i] - x))


def _text(words: list[dict]) -> str:
    return " ".join(w["text"] for w in sorted(words, key=lambda w: (round(w["top"]), w["x0"])))


class SubaruParser(BaseParser):
    brand = "subaru"
    powertrain = "EV"  # nominal default; Impreza/Forester rows are MHEV, see module docstring

    def parse(self, pdf_path: Path) -> list[ExtractedVariant]:
        """See module docstring for the two table shapes.

        Args:
            pdf_path: Local path to a downloaded Subaru price-list PDF.

        Returns:
            One `ExtractedVariant` per priced trim (x spec, for the EVs).
        """
        with pdfplumber.open(pdf_path) as pdf:
            match = _TITLE_RE.search(pdf.pages[0].extract_text() or "")
            model = _MODEL_NAMES[match.group(1).upper()] if match else "unknown"
            for page in pdf.pages[:3]:
                words = page.extract_words()
                texts = {w["text"] for w in words}
                if {"BEZ", "BONUSU", "SPECIFIKACE"} <= texts:
                    variants = self._parse_row_table(page, words, model)
                elif {"SPECIFIKACE", "včetně"} <= texts:
                    variants = self._parse_transposed_table(page, words, model)
                else:
                    continue
                if variants:
                    return variants
        return []

    @staticmethod
    def _parse_row_table(page: pdfplumber.page.Page, words: list[dict], model: str) -> list[ExtractedVariant]:
        """Args:
            page: The price page.
            words: Its words.
            model: The document's model.

        Returns:
            Impreza/Forester variants - see module docstring.
        """
        spec = next(w for w in words if w["text"] == "SPECIFIKACE")
        boxer = next(w for w in words if w["text"] == "BOXER")
        gearbox = next(w for w in words if w["text"] == "PŘEVODOVKA")
        header_row = [w for w in words if abs(w["top"] - next(x for x in words if x["text"] == "BONUSU")["top"]) < 1]
        vc = sorted((w for w in header_row if w["text"] == "VČ."), key=lambda w: w["x0"])
        bez_word = next(w for w in header_row if w["text"] == "BEZ")
        centers = [
            _center([bez_word, next(w for w in header_row if w["text"] == "DPH" and w["x0"] > bez_word["x0"])]),
            _center([vc[0], next(w for w in header_row if w["text"] == "DPH" and w["x0"] > vc[0]["x0"])]),
            _center([vc[1], next(w for w in header_row if w["text"] == "BONUSU")]),
        ]
        price_left = bez_word["x0"] - 15
        max_word = next(w for w in words if w["text"] == "MAX.")

        variants: list[ExtractedVariant] = []
        for row in _group_rows([w for w in words if w["top"] > spec["bottom"] + 2]):
            trim_words = [w for w in row if w["x1"] < boxer["x0"] - 5]
            prices = [w for w in row if w["x0"] >= price_left and w["text"].isdigit()]
            if not trim_words or not prices or not trim_words[0]["text"].isupper():
                continue
            row_top = row[0]["top"]
            columns: list[list[str]] = [[], [], []]
            for word in prices:
                columns[_nearest(_center([word]), centers)].append(word["text"])
            if not columns[1]:
                continue
            engine_words = [
                w
                for w in words
                if abs(w["top"] - row_top) <= _WRAP and spec["x1"] < w["x0"] and w["x1"] < gearbox["x0"] - 2
            ]
            transmission = _text([w for w in row if gearbox["x0"] - 20 <= w["x0"] < max_word["x0"] - 5])
            trim = _text(trim_words)
            engine = _text(engine_words)
            variants.append(
                ExtractedVariant(
                    model=model,
                    trim=trim,
                    variant_name=" ".join(part for part in (model, trim, engine, transmission) if part),
                    price=float("".join(columns[1])),
                    currency="CZK",
                    source_page=page.page_number,
                    raw_text=f"{engine} | {_text(row)}",
                    powertrain="MHEV",
                )
            )
        return variants

    @staticmethod
    def _parse_transposed_table(page: pdfplumber.page.Page, words: list[dict], model: str) -> list[ExtractedVariant]:
        """Args:
            page: The price page.
            words: Its words.
            model: The document's model.

        Returns:
            EV variants (Solterra/Uncharted/e-Outback) - see module
            docstring.
        """
        vat = min((w for w in words if w["text"] == "včetně"), key=lambda w: w["top"])
        spec = next(w for w in words if w["text"] == "SPECIFIKACE")
        trims = sorted(
            (w for w in words if vat["top"] - 14 < w["top"] < vat["top"] - 3 and w["x0"] > spec["x1"]),
            key=lambda w: w["x0"],
        )
        if not trims:
            return []
        centers = [_center([w]) for w in trims]
        label_right = trims[0]["x0"] - 30
        rows = _group_rows([w for w in words if w["top"] > vat["bottom"] + 2])
        # The table ends at the paint-surcharge line ("Příplatky za barvu
        # karoserie ... 20 000 Kč / 23 000 Kč") - its "Kč" amounts aren't prices.
        end = next((i for i, row in enumerate(rows) if row[0]["text"].startswith("Příplat")), len(rows))
        rows = rows[:end]
        details = [r for r in rows if r[0]["text"] == "kapacita"]
        # A spec label is printed on its price line (Uncharted) or on its own
        # line just above it (Solterra, e-Outback) - matched by shape.
        labels = [
            (row[0]["top"], [w for w in row if w["x1"] < label_right])
            for row in rows
            if _SPEC_LABEL_RE.match(_text([w for w in row if w["x1"] < label_right]))
        ]

        variants: list[ExtractedVariant] = []
        for row in rows:
            if not labels:
                break
            run: list[dict] = []
            cells: list[tuple[float, float]] = []
            for word in row:
                if word["x0"] < label_right:
                    continue
                if word["text"].isdigit():
                    run.append(word)
                elif word["text"] == "Kč" and run:
                    cells.append((_center(run), float("".join(w["text"] for w in run))))
                    run = []
                else:
                    run = []
            if not cells:
                continue
            row_top = row[0]["top"]
            label = min(labels, key=lambda item: abs(item[0] - row_top))[1]
            detail = min(details, key=lambda r: abs(r[0]["top"] - row_top), default=None)
            detail_text = _text(detail) if detail and abs(detail[0]["top"] - row_top) < 15 else ""
            kw = _KW_RE.search(detail_text)
            spec_text = _text(label) + (f" {kw.group(1)} kW" if kw else "")
            for x, price in cells:
                trim = trims[_nearest(x, centers)]["text"]
                variants.append(
                    ExtractedVariant(
                        model=model,
                        trim=trim,
                        variant_name=f"{model} {trim} {spec_text}",
                        price=price,
                        currency="CZK",
                        source_page=page.page_number,
                        raw_text=f"{_text(row)} | {detail_text}".strip(" |"),
                        powertrain="EV",
                    )
                )
        return variants
