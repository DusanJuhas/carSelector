"""Parser for KGM's (formerly SsangYong) per-model "Ceník" price lists
(verified against all eight real PDFs downloaded 2026-11-05 from
kgmcars.cz's widget CDN - Korando, Tivoli, Torres, Torres EVX, Actyon,
Rexton, Musso Grand and Musso EV; see scraper/tests/fixtures/kgm_*.pdf).

Every document's first priced page is a ruled table: a header row whose
cells are the trims (columns), then one row per engine with that trim's
price in each trim cell, then the trim's equipment rows ("S" standard,
"–" not available, a surcharge such as "49 900" for an option):

    STUPEŇ VÝBAVY            KÓD   CLUB         STYLE        PREMIUM
    1.5 GDI Turbo benzín – 163 k / 280 Nm   699 900      719 900      829 900
                                            569 900*     619 900*     729 900*
    Pohon všech kol (AWD) ...          PCA   49 900       49 900       49 900

The layouts differ in everything else (label column position, a "vč.
DPH" column, trims with a drive suffix - Rexton's "CLUB 2WD", Musso
Grand's "Style 4WD"), so rows are read through pdfplumber's own table
detection rather than line regexes. An engine row is one with a price of
at least `_MIN_PRICE` in a trim cell (option surcharges are far below).

A price cell can hold two or three numbers: the list price struck
through in a small font above the promotional price ("699 900" over
"569 900*"), the list price below the promotional one (Korando), or the
price without and with VAT (Musso Grand, a commercial pickup: "669 000 /
(809 490)"). In each case the wanted figure - the list price including
VAT, the same convention as every other brand here - is the largest
number in the cell. The struck-through and promotional prices overlap
vertically, so pdfplumber's word grouping interleaves their digits
("566969 9 90000*"); the cell's characters are therefore read one font
size at a time (`_cell_numbers`).

`model` comes from the engine label where it's printed ("Korando 1.5
Turbo GDI ...", "MUSSO EV - 80,6 kWh/FWD ..."). Torres and Actyon print
their name only as vector artwork, nowhere in the text, so for those the
document's own file name (`BaseParser.document_url`, e.g.
"202611_KGM_cenik_Actyon_CZ.pdf") is used; a document naming no known
model either way yields no variants rather than guessed ones.

Powertrain: a battery capacity ("kWh") -> EV; "Hybrid" (Torres/Actyon's
e-DHT full hybrid) -> HEV; otherwise ICE (petrol "GDI", diesel "e-XDI ...
diesel" - "diesel" stays in `variant_name` for the backend import). The
standard drive of a trim is read from the "Pohon ..." equipment rows
below its engine row (the one marked "S") and appended as FWD/RWD/AWD,
since Rexton's base trim is rear-wheel drive and the import reads drive
from the name. A decimal power ("152,2 kW") is rounded in `variant_name`
("152 kW") so the import's integer kW match reads it; `raw_text` keeps
the original. Release dates ("Ceník je platný od 16. 10. 2026") aren't in
`_pdf_layout.extract_release_date`'s shape, so `release_date` stays None.
Equipment isn't extracted."""

from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import unquote

import pdfplumber

from .base import BaseParser, ExtractedVariant

_TRIMS = {"style", "smart", "elegant", "premium", "club", "clever"}
# Longest/most specific first: "Torres EVX" before "Torres", "Musso EV"
# and "Musso Grand" before any bare "Musso".
_MODELS = ("Torres EVX", "Musso EV", "Musso Grand", "Rexton", "Korando", "Tivoli", "Actyon", "Torres")
_MIN_PRICE = 200_000
_NUMBER_RE = re.compile(r"\d{1,3}(?: \d{3})+")
_LABEL_PREFIX_RE = re.compile(r"^MOTORIZACE:?\s*", re.IGNORECASE)
_DECIMAL_KW_RE = re.compile(r"(\d+),\d+ kW\b")
_DRIVE_MARKERS = (("všech", "AWD"), ("zadních", "RWD"), ("předních", "FWD"))


def _clean(text: str | None) -> str:
    """Args:
        text: A table cell's text (may span lines), or `None`.

    Returns:
        The text on one line with whitespace collapsed.
    """
    return " ".join((text or "").split())


def _trim_name(cell: str | None) -> str | None:
    """Args:
        cell: A header-row cell, e.g. "CLUB\\n2WD", "Style 4WD", "PREMIUM".

    Returns:
        The trim with all-caps words re-cased ("Club 2WD", "Premium"), or
        `None` if the cell doesn't start with a known trim name.
    """
    words = _clean(cell).split()
    if not words or words[0].lower() not in _TRIMS:
        return None
    return " ".join(w.capitalize() if w.isalpha() else w for w in words)


def _model_in(text: str) -> str | None:
    """Args:
        text: Text to search, e.g. an engine label or a file name.

    Returns:
        The first of `_MODELS` found in `text` (case-insensitive,
        underscores/dashes read as spaces), or `None`.
    """
    haystack = re.sub(r"[_\-]+", " ", text).lower()
    for model in _MODELS:
        if model.lower() in haystack:
            return model
    return None


def _cell_numbers(page: pdfplumber.page.Page, bbox: tuple[float, float, float, float]) -> list[int]:
    """Args:
        page: The page the cell is on.
        bbox: The cell's bounding box.

    Returns:
        Every thousands-grouped number in the cell, read one font size at
        a time so overlapping struck-through and promotional prices don't
        interleave (see module docstring).
    """
    cell = page.within_bbox(bbox)
    numbers: list[int] = []
    for size in {round(char["size"], 1) for char in cell.chars}:
        same_size = cell.filter(lambda obj, s=size: obj.get("object_type") != "char" or round(obj["size"], 1) == s)
        text = same_size.extract_text() or ""
        numbers.extend(int(n.replace(" ", "")) for n in _NUMBER_RE.findall(text))
    return numbers


class KgmParser(BaseParser):
    brand = "kgm"
    powertrain = "ICE"  # nominal default; the actual powertrain is per-row, see _powertrain

    def parse(self, pdf_path: Path) -> list[ExtractedVariant]:
        """See module docstring for the table shape.

        Args:
            pdf_path: Local path to a downloaded KGM price-list PDF.

        Returns:
            One `ExtractedVariant` per engine x trim with a price.
        """
        url_model = _model_in(Path(unquote(self.document_url)).name) if self.document_url else None
        variants: list[ExtractedVariant] = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                tables = page.find_tables()
                page_drives = self._page_drives([table.extract() for table in tables])
                for table in tables:
                    variants.extend(self._parse_table(page, table, url_model, page_drives))
        return variants

    @classmethod
    def _page_drives(cls, tables: list[list[list[str | None]]]) -> dict[str, str]:
        """Args:
            tables: Every table on a page, as cell texts.

        Returns:
            Trim -> its standard drive marker, read from whichever table on
            the page holds the "Pohon ..." rows (Korando and Rexton print
            them in an equipment table below the price table, not under
            the engine row).
        """
        drives: dict[str, str] = {}
        for texts in tables:
            trims: dict[int, str] = {}
            for index, cells in enumerate(texts):
                header = {j: name for j, cell in enumerate(cells) if (name := _trim_name(cell))}
                if header:
                    trims = header
                    for j, trim in trims.items():
                        if trim not in drives and (drive := cls._standard_drive(texts[index + 1 :], j)):
                            drives[trim] = drive
        return drives

    def _parse_table(
        self,
        page: pdfplumber.page.Page,
        table: pdfplumber.table.Table,
        url_model: str | None,
        page_drives: dict[str, str],
    ) -> list[ExtractedVariant]:
        """Args:
            page: The page the table is on.
            table: One detected table.
            url_model: The model named by the document's file name, if any.
            page_drives: Trim -> standard drive from anywhere on the page
                (see `_page_drives`), the fallback when the engine row has
                no "Pohon ..." rows of its own below it.

        Returns:
            The table's variants - `[]` for a table without a trim header
            or engine rows.
        """
        rows = table.rows
        texts = table.extract()
        trims: dict[int, str] = {}
        variants: list[ExtractedVariant] = []
        engine_rows: list[tuple[int, str, dict[int, tuple[int, str]]]] = []
        for index, cells in enumerate(texts):
            header = {j: name for j, cell in enumerate(cells) if (name := _trim_name(cell))}
            if header:
                trims = header
                continue
            if not trims:
                continue
            prices: dict[int, tuple[int, str]] = {}
            for j in trims:
                bbox = rows[index].cells[j] if j < len(rows[index].cells) else None
                if bbox is None or sum(ch.isdigit() for ch in cells[j] or "") < 6:
                    continue
                numbers = _cell_numbers(page, bbox)
                if numbers and max(numbers) >= _MIN_PRICE:
                    prices[j] = (max(numbers), _clean(cells[j]))
            if prices:
                label = self._label(cells, trims)
                engine_rows.append((index, label, prices))

        for position, (index, label, prices) in enumerate(engine_rows):
            model = _model_in(label) or url_model
            if model is None:
                continue
            end = engine_rows[position + 1][0] if position + 1 < len(engine_rows) else len(texts)
            for j, (price, cell_text) in prices.items():
                drive = self._standard_drive(texts[index + 1 : end], j) or page_drives.get(trims[j])
                variants.append(self._variant(model, trims[j], label, drive, price, cell_text, page.page_number))
        return variants

    @staticmethod
    def _label(cells: list[str | None], trims: dict[int, str]) -> str:
        """Args:
            cells: An engine row's cell texts.
            trims: Column index -> trim, to skip the price cells.

        Returns:
            The engine label - the longest non-trim cell containing a digit
            (the side labels are rotated text with none), with a leading
            "MOTORIZACE" dropped.
        """
        candidates = [_clean(c) for j, c in enumerate(cells) if j not in trims and any(ch.isdigit() for ch in c or "")]
        label = max(candidates, key=len, default="")
        return _LABEL_PREFIX_RE.sub("", label)

    @staticmethod
    def _standard_drive(rows: list[list[str | None]], column: int) -> str | None:
        """Args:
            rows: The equipment rows between this engine row and the next.
            column: The trim's column index.

        Returns:
            "AWD", "RWD" or "FWD" for the first "Pohon ..." row marked "S"
            for this trim, or `None` if there is none.
        """
        for cells in rows:
            if column >= len(cells) or _clean(cells[column]) != "S":
                continue
            label = " ".join(_clean(c) for j, c in enumerate(cells) if j != column).lower()
            if "pohon" not in label:
                continue
            for needle, marker in _DRIVE_MARKERS:
                if needle in label:
                    return marker
        return None

    @staticmethod
    def _variant(
        model: str, trim: str, label: str, drive: str | None, price: int, cell_text: str, page_number: int
    ) -> ExtractedVariant:
        """Args:
            model: The model nameplate.
            trim: The trim (column header).
            label: The engine label as printed.
            drive: The trim's standard drive marker, or `None`.
            price: The list price incl. VAT.
            cell_text: The price cell as printed.
            page_number: 1-based page the row is on.

        Returns:
            The variant for this engine x trim.
        """
        engine = re.sub(rf"^{re.escape(model)}\s*-?\s*", "", label, flags=re.IGNORECASE)
        engine = _DECIMAL_KW_RE.sub(r"\1 kW", engine)
        lowered = label.lower()
        if "kwh" in lowered:
            powertrain = "EV"
        elif "hybrid" in lowered:
            powertrain = "HEV"
        else:
            powertrain = "ICE"
        return ExtractedVariant(
            model=model,
            trim=trim,
            variant_name=" ".join(part for part in (model, trim, engine, drive) if part),
            price=float(price),
            currency="CZK",
            source_page=page_number,
            raw_text=f"{label} | {trim} | {cell_text}",
            powertrain=powertrain,
        )
