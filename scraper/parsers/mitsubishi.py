"""Parser for Mitsubishi's per-model "Ceník" price lists (verified against
all ten real PDFs downloaded 2026-11-02 from mitsubishi-motors.cz, valid
1-30 November 2026 - see scraper/tests/fixtures/mitsubishi_*.pdf).
Covers Colt (petrol and its separate Hybrid document), ASX (plus its
"Limited" special edition), Grandis, Eclipse Cross BEV and Outlander PHEV
(plus its "Black Edition", "Diamond" and "25 let" special-edition
documents) - every personal car Mitsubishi sells in CZ.

Every document has the same 12-page brochure template; the price table
is always on page 3, under a "CENÍK <MODEL>" heading, as one row per
trim x engine:

    Výbava    Motor             Výkon            Převodovka  Pohon  Cena          Sleva      Akční cena
    INFORM    1.2 DI-T          84 kW / 115 k    6MT         2WD    513 790 Kč    15 000 Kč  498 790 Kč

`price` is "Cena" (the list price) - "Sleva"/"Akční cena" (discount and
resulting promotional price, absent on some documents) are read then
discarded, same "list price, not a promotional one" convention as every
other brand here. Eclipse Cross BEV's own table has no "Motor" column
and a "Kapacita baterie" ("87 kWh") one after "Výkon" instead -
`_ROW_RE`'s optional battery group covers both shapes.

The "Výbava" (trim) cell is vertically MERGED across all of a trim's
rows (ASX's "INVITE+" spans two engine rows, its label printed once,
centred between them) - the same problem MG's/Opel's `_nearest_trim`
solves by vertical distance. Here that heuristic is ambiguous (ASX's own
INTENSE+ group is 3 rows high, so its last row is exactly as far from
the INTENSE+ label as from the next group's INSTYLE label), but the table
draws its own cell borders: horizontal rules across the trim column
exist only at trim-group boundaries (verified on all ten fixtures via
`page.edges`). `_trim_bands` reads those, and each row takes the label
inside its own band.

Rows below the table that also mention "Kč" ("PAKET TRAIL 69 990 Kč",
optional packages on Outlander's documents) don't carry a "kW / k" power
figure, so `_ROW_RE` doesn't match them.

`model` is read from the "CENÍK ..." heading and normalized to the
nameplate (`_MODEL_PREFIXES`): "CENÍK NOVÝ COLT Hybrid" -> "Colt",
"CENÍK OUTLANDER PHEV 4x4 25 LET" -> "Outlander PHEV", "CENÍK ASX
LIMITED" -> "ASX". The special edition itself is already the row's own
trim label ("LIMITED", "BLACK EDITION", "DIAMOND TOP", "25 LET
OUTLANDER"), so it isn't lost.

Powertrain is classified per row from the engine text: "MILD HYBRID" ->
MHEV, "HYBRID (HEV)" -> HEV, "elektromotor" (Outlander's "2.4 DOHC MIVEC
+ 2x elektromotor") -> PHEV, a battery capacity in kWh -> EV, everything
else (MPI, DI-T petrol) -> ICE.

Every cover page reads "Platnost ceníku D. M. RRRR do D. M. RRRR" - a
one-month validity window, like Kia's own promotional "Platnost ceníku
od ... - ..." - which `_pdf_layout.extract_release_date` deliberately
doesn't match, so `release_date` stays None (download date used instead).
The "KLÍČOVÉ PRVKY" (key features) bullets under the table aren't
extracted as equipment."""

from __future__ import annotations

import re
from pathlib import Path

import pdfplumber

from ._pdf_layout import group_into_lines, line_text
from .base import BaseParser, ExtractedVariant

_PRICE_PAGE_TITLE = "CENÍK "
_MODEL_PREFIXES = (
    ("ECLIPSE CROSS", "Eclipse Cross"),
    ("OUTLANDER", "Outlander PHEV"),
    ("GRANDIS", "Grandis"),
    ("COLT", "Colt"),
    ("ASX", "ASX"),
)
_ROW_RE = re.compile(
    r"^(?P<engine>.*?)\s*(?P<kw>\d+)\s*kW\s*/\s*\d+\s*k\s+"
    r"(?:(?P<battery>[\d,.]+)\s*kWh\s+)?"
    r"(?P<transmission>.+?)\s+(?P<drive>[24]WD(?:\s+S-AWC)?)\s+"
    r"(?P<price>\d{1,3}(?: \d{3})+)\s*Kč"
)


def _classify_powertrain(engine: str, battery: str | None) -> str:
    if battery is not None:
        return "EV"
    lowered = engine.lower()
    if "mild hybrid" in lowered:
        return "MHEV"
    if "hybrid" in lowered:
        return "HEV"
    if "elektromotor" in lowered:
        return "PHEV"
    return "ICE"


def _normalize_model(title: str) -> str:
    """Args:
        title: The price page's own heading, e.g. "CENÍK NOVÝ COLT Hybrid".

    Returns:
        The nameplate (see module docstring), or "unknown".
    """
    upper = title.upper()
    for prefix, model in _MODEL_PREFIXES:
        if prefix in upper:
            return model
    return "unknown"


def _trim_bands(page: pdfplumber.page.Page, left: float, right: float, top: float) -> list[float]:
    """Args:
        page: The price page.
        left: x0 of the "Výbava" header word (the trim column's text start).
        right: x0 of the next header word (the trim column's right edge).
        top: `top` of the header row.

    Returns:
        Sorted, de-duplicated `top`s of the horizontal rules spanning the
        trim column below the header - the boundaries between trim groups
        (see module docstring).
    """
    tops = sorted(
        e["top"]
        for e in page.edges
        if e["orientation"] == "h" and e["x0"] <= left and e["x1"] >= right - 5 and e["top"] > top
    )
    bands: list[float] = []
    for value in tops:
        if not bands or value - bands[-1] > 1.0:
            bands.append(value)
    return bands


class MitsubishiParser(BaseParser):
    brand = "mitsubishi"
    powertrain = "ICE"  # nominal default; the actual powertrain is per-row, see _classify_powertrain

    def parse(self, pdf_path: Path) -> list[ExtractedVariant]:
        """See module docstring for the table shape and trim-cell handling.

        Args:
            pdf_path: Local path to a downloaded Mitsubishi price-list PDF.

        Returns:
            One `ExtractedVariant` per price row of the "CENÍK ..." table.
        """
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                variants = self._parse_page(page)
                if variants:
                    return variants
        return []

    def _parse_page(self, page: pdfplumber.page.Page) -> list[ExtractedVariant]:
        """Args:
            page: One page of the brochure.

        Returns:
            The page's price rows, or `[]` if it has no "Výbava ... Cena"
            header (every page but the price page).
        """
        words = page.extract_words()
        lines = group_into_lines(words)
        header = next(
            (ln for ln in lines if ln[0]["text"] == "Výbava" and any(w["text"] == "Cena" for w in ln)),
            None,
        )
        if header is None or len(header) < 2:
            return []
        title_line = next((ln for ln in lines if line_text(ln).startswith(_PRICE_PAGE_TITLE)), None)
        model = _normalize_model(line_text(title_line)) if title_line else "unknown"

        trim_left = header[0]["x0"]
        trim_right = header[1]["x0"]
        header_top = header[0]["top"]
        bands = _trim_bands(page, trim_left, trim_right, header_top)

        below = [w for w in words if w["top"] > header_top + 2]
        content_lines = group_into_lines([w for w in below if w["x0"] >= trim_right - 2])
        label_words = [w for w in below if w["x1"] < trim_right]

        variants: list[ExtractedVariant] = []
        for line in content_lines:
            text = line_text(line)
            match = _ROW_RE.match(text)
            if match is None:
                continue
            row_top = line[0]["top"]
            trim = self._trim_for_row(row_top, bands, label_words)

            engine = match.group("engine").strip()
            battery = match.group("battery")
            power = f"{battery} kWh" if battery else engine
            spec = f"{power} {match.group('kw')} kW {match.group('transmission')} {match.group('drive')}"
            variants.append(
                ExtractedVariant(
                    model=model,
                    trim=trim,
                    variant_name=f"{model} {trim or ''} {spec}".replace("  ", " ").strip(),
                    price=float(match.group("price").replace(" ", "")),
                    currency="CZK",
                    source_page=page.page_number,
                    raw_text=f"{trim} | {text}" if trim else text,
                    powertrain=_classify_powertrain(engine, battery),
                )
            )
        return variants

    @staticmethod
    def _trim_for_row(row_top: float, bands: list[float], label_words: list[dict]) -> str | None:
        """Args:
            row_top: `top` of the data row.
            bands: Trim-group boundaries from `_trim_bands`.
            label_words: Every word in the trim column below the header.

        Returns:
            The label inside the band that contains `row_top` (words in
            reading order), or - if the page has no usable rules - the
            vertically nearest label line, MG's own fallback. `None` if
            no label is found at all.
        """
        upper = next((b for b in bands if b > row_top), None)
        lower = max((b for b in bands if b <= row_top), default=None)
        if upper is not None and lower is not None:
            inside = [w for w in label_words if lower <= w["top"] < upper]
        else:
            inside = []
        if not inside and label_words:
            nearest_top = min(label_words, key=lambda w: abs(w["top"] - row_top))["top"]
            inside = [w for w in label_words if abs(w["top"] - nearest_top) <= 1.0]
        if not inside:
            return None
        return " ".join(w["text"] for w in sorted(inside, key=lambda w: (round(w["top"]), w["x0"])))
