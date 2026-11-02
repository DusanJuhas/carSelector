"""Parser for Nissan's per-model "Ceník" price lists (verified against all
five real PDFs downloaded 2026-11-02 from nissan-cdn.net, the ones
nissan.cz's own homepage links - see scraper/tests/fixtures/nissan_*.pdf).
Covers Micra, Juke, Qashqai, X-Trail and the X-Trail "Summer Edition".
Interstar/Townstar (commercial vehicles) aren't covered; Ariya has a
brochure but no price list.

Nissan's pages are the busiest of any brand here: every page is a 540pt
wide sheet with marketing panels printed BEYOND its right edge (Juke's
second "Akční cena / Ceníková cena" summary table, Qashqai's "Již od
599.990 Kč", the finance offer) and colour-swatch labels ("R 255 G 255
B 255") at negative x - so only words with 0 <= x0 < page width are read
at all. Two table shapes remain:

**Juke / Qashqai / X-Trail** - one row per trim x engine:

    Výbava      Verze                       Výkon            Ceníková cena  Sleva     Akční cena
                1.3 DIG-T mHEV 2WD, 6MT                                                          (wrapped)
    ACENTA      e-POWER, 2WD                151 kW (205 k)   939990Kč       150 000 Kč  789 990 Kč
                + COMFORT PACK                                                                   (wrapped)

Every word is assigned to the column whose header is horizontally
nearest (the columns are centred, so header and text don't share left
edges). Each row is anchored on its "Ceníková cena" cell - the list
price, used as `price`; Sleva/Akční cena are read then discarded, the
same convention as every other brand here. The list price is printed
inconsistently even within one table ("784 990Kč", "829990Kč",
"1 004 990Kč", "599 900" with no "Kč"), so the cell's digits are simply
concatenated. Engine ("Verze") and power ("Výkon") words join the
vertically nearest anchor (they wrap a line above/below), and the trim
("Výbava") label, printed once centred on its group of rows, does too.
Qashqai's engine column also carries a stray offer line ("Nabídka platí
na skladové vozy do 31. 10.") - cut at "Nabídka".

**Micra** - transposed: trims are columns (ENGAGE, ADVANCE, EVOLVE), and
each battery ("40 kWh –120k") has a "Ceníková cena" row whose prices sit
under the trims that offer it. Each price (digit run ended by "Kč") goes
to the nearest trim column; the battery label is the nearest "kWh" line.

`model` comes from the title ("CENÍK – NISSAN X-TRAIL SUMMER EDITION",
or Micra's cover "NISSAN / MICRA"); a Summer Edition document's trims get
" Summer Edition" appended so they don't collide with the regular
X-Trail's trims of the same name. Powertrain from the engine: kWh -> EV;
"mHEV" -> MHEV; "e-POWER" (series hybrid) or "HEV" -> HEV; other petrol
("DIG-T") -> ICE. No release date is read (each document words its
validity differently, none as "Platnost od D. M. RRRR")."""

from __future__ import annotations

import re
from pathlib import Path

import pdfplumber

from .base import BaseParser, ExtractedVariant

_TITLE_RE = re.compile(r"NISSAN\s+(MICRA|JUKE|QASHQAI|X-TRAIL)(\s+SUMMER EDITION)?", re.IGNORECASE)
_MODEL_NAMES = {"MICRA": "Micra", "JUKE": "Juke", "QASHQAI": "Qashqai", "X-TRAIL": "X-Trail"}
_KW_RE = re.compile(r"(\d+)\s*kW")
_ANCHOR_TOLERANCE = 2.0  # pt; the list-price cell's own words share `top` within this
_LABEL_LINE_GAP = 14.0  # pt; lines of one wrapped trim label (~12pt) vs. separate labels (40pt+)
# First section after the price table: equipment ("HLAVNÍ PRVKY VÝBAVY",
# "HLAVNÍ VÝBAVA"), optional extras ("VOLITELNÁ ...") or the finance offer.
_TABLE_END_WORDS = {"HLAVNÍ", "VOLITELNÁ", "Zvýhodněné"}


def _center(word: dict) -> float:
    return (word["x0"] + word["x1"]) / 2


def _nearest(value: float, values: list[float]) -> int:
    return min(range(len(values)), key=lambda i: abs(values[i] - value))


def _text(words: list[dict]) -> str:
    return " ".join(w["text"] for w in sorted(words, key=lambda w: (round(w["top"]), w["x0"])))


def _classify_powertrain(engine: str) -> str:
    if "kWh" in engine:
        return "EV"
    if "mHEV" in engine:
        return "MHEV"
    if "e-POWER" in engine or re.search(r"\bHEV\b", engine):
        return "HEV"
    return "ICE"


class NissanParser(BaseParser):
    brand = "nissan"
    powertrain = "ICE"  # nominal default; the actual powertrain is per-row, see _classify_powertrain

    def parse(self, pdf_path: Path) -> list[ExtractedVariant]:
        """See module docstring for the two table shapes.

        Args:
            pdf_path: Local path to a downloaded Nissan price-list PDF.

        Returns:
            One `ExtractedVariant` per priced row (Juke/Qashqai/X-Trail)
            or trim x battery cell (Micra).
        """
        with pdfplumber.open(pdf_path) as pdf:
            title_text = " ".join((page.extract_text() or "") for page in pdf.pages[:4])
            match = _TITLE_RE.search(title_text)
            model = _MODEL_NAMES[match.group(1).upper()] if match else "unknown"
            edition = " Summer Edition" if match and match.group(2) else ""
            for page in pdf.pages:
                words = [w for w in page.extract_words() if 0 <= w["x0"] < page.width]
                texts = {w["text"] for w in words}
                if {"Výbava", "Verze", "Výkon"} <= texts:
                    variants = self._parse_row_table(page, words, model, edition)
                elif "Model" in texts and "Ceníkovácena" in texts:
                    variants = self._parse_transposed_table(page, words, model)
                else:
                    continue
                if variants:
                    return variants
        return []

    @staticmethod
    def _parse_row_table(
        page: pdfplumber.page.Page, words: list[dict], model: str, edition: str
    ) -> list[ExtractedVariant]:
        """Args:
            page: The price page.
            words: Its on-page words.
            model: The document's model.
            edition: " Summer Edition" or "".

        Returns:
            Juke/Qashqai/X-Trail variants - see module docstring.
        """

        def header(*names: str) -> dict:
            return next(w for w in words if w["text"] in names)

        columns = {
            "trim": header("Výbava"),
            "engine": header("Verze"),
            "power": header("Výkon"),
            "list": header("Ceníková", "Ceníkovácena"),
            "discount": header("Sleva"),
            "promo": header("Akční", "Akčnícena"),
        }
        names = list(columns)
        centers = [_center(columns[name]) for name in names]
        # The table starts below the lowest header word ("Kč vč. DPH") and
        # ends at the first section below it - see `_TABLE_END_WORDS`.
        body_top = max(w["bottom"] for w in words if w["text"] == "DPH" and w["top"] < columns["trim"]["top"] + 30)
        end = min(
            [w["top"] for w in words if w["text"] in _TABLE_END_WORDS and w["top"] > body_top]
            + [w["top"] - 15 for w in words if w["text"] in ("(Navíc", "(navíc") and w["top"] > body_top]
            + [page.height]
        )
        body = [w for w in words if body_top < w["top"] < end]
        by_column: dict[str, list[dict]] = {name: [] for name in names}
        trim_right = columns["trim"]["x1"] + 2
        for word in body:
            if word["x0"] < trim_right:
                by_column["trim"].append(word)
            else:
                # Only the trim column starts in the left margin - an
                # engine's own wrapped "+ ColdPack" line, centred nearer the
                # "Výbava" header than "Verze", must still count as engine.
                index = _nearest(_center(word), centers[1:]) + 1
                by_column[names[index]].append(word)

        anchors: list[list[dict]] = []
        for word in sorted(by_column["list"], key=lambda w: w["top"]):
            if not re.search(r"\d", word["text"]):
                continue
            if anchors and abs(anchors[-1][0]["top"] - word["top"]) <= _ANCHOR_TOLERANCE:
                anchors[-1].append(word)
            else:
                anchors.append([word])
        anchors = [a for a in anchors if len(re.sub(r"\D", "", "".join(w["text"] for w in a))) >= 5]
        if not anchors:
            return []
        tops = [a[0]["top"] for a in anchors]

        def assign(column: str) -> list[list[dict]]:
            groups: list[list[dict]] = [[] for _ in anchors]
            for word in by_column[column]:
                groups[_nearest(word["top"], tops)].append(word)
            return groups

        engines, powers = assign("engine"), assign("power")
        # A trim label can wrap ("N-DESIGN," / "N-SPORT" - one label for a
        # group), so label lines close together form one block, centred on
        # its group of rows; each row takes the nearest block.
        blocks: list[list[dict]] = []
        for word in sorted(by_column["trim"], key=lambda w: w["top"]):
            if blocks and word["top"] - blocks[-1][-1]["top"] <= _LABEL_LINE_GAP:
                blocks[-1].append(word)
            else:
                blocks.append([word])
        block_centers = [(b[0]["top"] + b[-1]["top"]) / 2 for b in blocks]

        variants: list[ExtractedVariant] = []
        for index, anchor in enumerate(anchors):
            engine = _text(engines[index]).split(" Nabídka")[0].strip()
            power = _text(powers[index])
            trim_words = blocks[_nearest(tops[index], block_centers)] if blocks else []
            trim = _text(trim_words) + edition if trim_words else None
            if not engine:
                continue
            kw = _KW_RE.search(power)
            spec = f"{engine} {kw.group(1)} kW" if kw else engine
            variants.append(
                ExtractedVariant(
                    model=model,
                    trim=trim,
                    variant_name=f"{model} {trim or ''} {spec}".replace("  ", " ").strip(),
                    price=float(re.sub(r"\D", "", "".join(w["text"] for w in anchor))),
                    currency="CZK",
                    source_page=page.page_number,
                    raw_text=" | ".join(part for part in (trim, engine, power, _text(anchor)) if part),
                    powertrain=_classify_powertrain(engine),
                )
            )
        return variants

    @staticmethod
    def _parse_transposed_table(page: pdfplumber.page.Page, words: list[dict], model: str) -> list[ExtractedVariant]:
        """Args:
            page: The price page.
            words: Its on-page words.
            model: The document's model.

        Returns:
            Micra variants - see module docstring.
        """
        header_word = next(w for w in words if w["text"] == "Model")
        trims = sorted(
            (w for w in words if abs(w["top"] - header_word["top"]) < 3 and w["x0"] > header_word["x1"] + 50),
            key=lambda w: w["x0"],
        )
        if not trims:
            return []
        centers = [_center(w) for w in trims]
        battery_rows = sorted(
            {round(w["top"], 1) for w in words if w["text"] == "kWh" and w["x0"] < trims[0]["x0"] - 50}
        )

        variants: list[ExtractedVariant] = []
        for label in (w for w in words if w["text"] == "Ceníkovácena"):
            row = sorted(
                (w for w in words if abs(w["top"] - label["top"]) <= 3 and w["x0"] > label["x1"]),
                key=lambda w: w["x0"],
            )
            if not battery_rows:
                break
            battery_top = battery_rows[_nearest(label["top"], battery_rows)]
            battery = _text([w for w in words if abs(w["top"] - battery_top) < 1 and w["x0"] < trims[0]["x0"] - 50])
            run: list[dict] = []
            for word in row:
                if word["text"].isdigit():
                    run.append(word)
                    continue
                if word["text"] == "Kč" and run:
                    trim = trims[_nearest((run[0]["x0"] + word["x1"]) / 2, centers)]["text"]
                    variants.append(
                        ExtractedVariant(
                            model=model,
                            trim=trim,
                            variant_name=f"{model} {trim} {battery}",
                            price=float("".join(w["text"] for w in run)),
                            currency="CZK",
                            source_page=page.page_number,
                            raw_text=f"{battery} | {_text(row)}",
                            powertrain="EV",
                        )
                    )
                run = []
        return variants
