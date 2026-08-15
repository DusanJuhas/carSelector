#!/usr/bin/env python3
"""Imports scraper's parsed price-list data (storage/scraper.db) into the
backend's normalized catalog (storage/drivewise.db, or wherever
DATABASE_URL points).

scraper/ and backend/ deliberately use two different schemas (document-
centric vs. normalized catalog) with no live pipeline between them - see
storage/README.md and the drivewise-data-model skill. This script is that
missing one-way import step. It's a standalone script, not part of either
service's request path - run it manually after a scrape:

    python scripts/import_scraper_data.py [--dry-run]

Safe to re-run: brands/models/trims/powertrains/configurations are looked
up by natural key before creating, and prices only get a new row when the
price actually changed (closing the previous one) - matching the
append-only design in app/models/price.py.

What it deliberately does NOT import (documented gaps, not silently
dropped):
- Equipment/options: scraper's equipment_assignment never carries a
  surcharge amount, but drivewise's option_availability requires one for
  'optional' rows (a CHECK constraint) - importing would mean fabricating
  a price. Skipped entirely for now.
- model.category (body type), model_year, colors, and most of
  powertrains' spec columns (transmission, displacement_cc, consumption,
  co2, ...): none of these are structured fields in scraper's schema, only
  free text in variant_name/raw_text. Left null, same "not derivable from
  the source" stance already documented for the hand-seeded fixtures.
- fuel_type/drivetrain ARE inferred from variant_name text (see
  infer_fuel_type/infer_drivetrain below) since drivewise requires them
  (NOT NULL) - this is a heuristic, not a parse of a structured field, and
  can be wrong on unusual naming. power_kw is opportunistically extracted
  the same way, staying None where no reliable "NNN kW" substring exists
  (e.g. Toyota's price lists only state hp, not kW).

Note: `powertrains.manufacturer_code` is repurposed here to hold a
fingerprint of this script's own dedup key (see signature_fingerprint),
not a real manufacturer order code - only rows created by this script use
it that way.

Code style: the free functions below (slugify, infer_fuel_type, ...) are
small, stateless, single-purpose helpers with no shared state - per
drivewise-architecture's Code style section, they stay plain functions.
`ScraperDataImporter` is the opposite case (a run's per-brand/model/trim/
powertrain/configuration/source-document caches genuinely are shared,
mutated state across every get_or_create_* call for that run) - a class,
with the caches as instance attributes instead of a dict threaded through
every function call.
"""
from __future__ import annotations

import argparse
import hashlib
import re
import sqlite3
import sys
import unicodedata
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "backend"))

from sqlalchemy import select  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.db.session import SessionLocal  # noqa: E402
from app.models import (  # noqa: E402
    Brand,
    CarModel,
    Configuration,
    Powertrain,
    Price,
    SourceDocument,
    Trim,
)
from app.models.enums import DocumentType, Drivetrain, FuelType  # noqa: E402

SCRAPER_DB_PATH = REPO_ROOT / "storage" / "scraper.db"
MARKET = "CZ"
LOCALE = "cs-CZ"

# scraper/'s source_brand keys are already valid slugs (lowercase, no
# accents); only the display name needs real casing/diacritics.
BRAND_NAMES = {
    "skoda": "Škoda",
    "volkswagen": "Volkswagen",
    "kia": "Kia",
    "toyota": "Toyota",
}

_SCRAPER_TO_FUEL_TYPE = {
    "EV": FuelType.electric,
    "MHEV": FuelType.mild_hybrid,
    "PHEV": FuelType.phev,
    "HEV": FuelType.hybrid,
    # "ICE" is ambiguous (petrol vs. diesel) - resolved in infer_fuel_type.
}

_KW_RE = re.compile(r"(\d+)\s*kW", re.IGNORECASE)
_AWD_RE = re.compile(r"4x4|4motion|awd|quattro|4matic", re.IGNORECASE)
_DIESEL_RE = re.compile(r"\bTDI\b|\bCRDI\b|diesel", re.IGNORECASE)


def slugify(text: str) -> str:
    """Args:
        text: Free-text name to turn into a URL/slug-safe identifier.

    Returns:
        `text` lowercased, with diacritics stripped and any run of
        non-alphanumeric characters collapsed to a single hyphen (leading/
        trailing hyphens removed). `"x"` if that leaves nothing (e.g.
        `text` was purely punctuation).
    """
    normalized = unicodedata.normalize("NFKD", text)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_text).strip("-").lower()
    return slug or "x"


def infer_fuel_type(scraper_powertrain: str, variant_name: str) -> FuelType:
    """Args:
        scraper_powertrain: scraper's own `variant.powertrain` value -
            one of `"ICE"`, `"EV"`, `"MHEV"`, `"PHEV"`, `"HEV"`.
        variant_name: The variant's display name, used only to split
            `"ICE"` into petrol/diesel (the other values map directly).

    Returns:
        The drivewise `FuelType` this variant most likely is. Every value
        except `"ICE"` maps 1:1 via `_SCRAPER_TO_FUEL_TYPE`; `"ICE"`
        resolves to `diesel` if `variant_name` contains a diesel marker
        (TDI/CRDI/"diesel"), else `petrol`.
    """
    if scraper_powertrain in _SCRAPER_TO_FUEL_TYPE:
        return _SCRAPER_TO_FUEL_TYPE[scraper_powertrain]
    # scraper_powertrain == "ICE": split into petrol/diesel from the name.
    return FuelType.diesel if _DIESEL_RE.search(variant_name) else FuelType.petrol


def infer_drivetrain(variant_name: str) -> Drivetrain:
    """Args:
        variant_name: The variant's display name to scan for an
            AWD/4x4-style marker (4x4, 4Motion, AWD, quattro, 4MATIC).

    Returns:
        `Drivetrain.awd` if a marker was found, else `Drivetrain.fwd`.
        RWD isn't distinguishable from the naming these brands use for
        these segments (no rear-drive models in this data) - default to
        fwd, the overwhelming majority, rather than guess at rwd.
    """
    return Drivetrain.awd if _AWD_RE.search(variant_name) else Drivetrain.fwd


def extract_power_kw(text: str) -> int | None:
    """Args:
        text: Free text to search for a "NNN kW" substring.

    Returns:
        The first power figure found in kW, or `None` if `text` has no
        such substring (e.g. Toyota's price lists only state hp).
    """
    m = _KW_RE.search(text)
    return int(m.group(1)) if m else None


def powertrain_signature(variant_name: str, trim: str) -> str:
    """A stable per-model dedup key for 'the same engine' across trims -
    the variant name with the (already separately tracked) trim name
    removed, since scraper's variant_name = model + trim + engine spec in
    an order that differs by brand (trim is sometimes in the middle,
    sometimes at the end) - see this script's module docstring.

    Args:
        variant_name: scraper's `variant.variant_name` for this row.
        trim: The already-extracted trim name to strip out of
            `variant_name`, wherever it occurs.

    Returns:
        `variant_name` with the first occurrence of `trim` removed,
        whitespace-collapsed and lowercased. Two variants within the same
        model that resolve to the same signature are treated as the same
        underlying engine (see `ScraperDataImporter.get_or_create_powertrain`).
    """
    remainder = variant_name.replace(trim, "") if trim else variant_name
    return re.sub(r"\s+", " ", remainder).strip().lower()


def signature_fingerprint(signature: str) -> str:
    """Short, deterministic stand-in for `signature` that fits in
    Powertrain.manufacturer_code (String(32)) - used as the persisted
    identity for matching 'the same engine' across separate runs of this
    script (see ScraperDataImporter.get_or_create_powertrain).
    (fuel_type, drivetrain, power_kw) alone isn't a reliable identity:
    two genuinely different engines within a model can share all three
    (e.g. two similarly-tuned petrol FWD variants), so a rerun without
    this would risk silently merging or splitting powertrains rather
    than matching the exact one this script created originally.

    Args:
        signature: Output of `powertrain_signature` to fingerprint.

    Returns:
        A short, deterministic, collision-resistant-enough string
        (`"scr:"` + 24 hex chars of a SHA-256 digest) safe to store in a
        `String(32)` column.
    """
    return "scr:" + hashlib.sha256(signature.encode("utf-8")).hexdigest()[:24]


@dataclass
class ImportStats:
    """Counts accumulated over one `ScraperDataImporter.run()` call, for
    the end-of-run summary printout."""

    brands: int = 0
    models: int = 0
    trims: int = 0
    powertrains: int = 0
    configurations: int = 0
    source_documents: int = 0
    prices_inserted: int = 0
    prices_unchanged: int = 0
    equipment_skipped: int = 0
    warnings: list[str] = field(default_factory=list)


class ScraperDataImporter:
    """Imports one scraper.db's worth of documents/variants/prices into a
    backend DB session, per this module's docstring. One instance = one
    import run: the natural-key caches below are genuinely per-run
    mutable state shared across every `get_or_create_*` call, which is
    exactly the "real behavior grouped around state" case for a class
    per `drivewise-architecture`'s Code style section.
    """

    def __init__(self, db: Session, scraper_con: sqlite3.Connection) -> None:
        """Args:
            db: Backend database session to write the imported catalog
                into. Not committed by this class - the caller commits
                (or rolls back, for `--dry-run`) after `run()` returns.
            scraper_con: Read-only connection to scraper.db to import from.
        """
        self._db = db
        self._scraper_con = scraper_con
        self.stats = ImportStats()
        self._brand_cache: dict[str, Brand] = {}
        self._model_cache: dict[tuple[int, str], CarModel] = {}
        self._trim_cache: dict[tuple[int, str], Trim] = {}
        self._powertrain_cache: dict[tuple[int, str], Powertrain] = {}
        self._configuration_cache: dict[tuple[int, int], Configuration] = {}
        self._source_document_cache: dict[str, SourceDocument] = {}

    def get_or_create_brand(self, slug: str) -> Brand:
        """Args:
            slug: scraper's `source_brand` value (already a valid slug).

        Returns:
            The existing `Brand` row for `slug`, or a newly created one
            (display name from `BRAND_NAMES`, falling back to
            `slug.title()` for an unmapped brand).
        """
        if slug in self._brand_cache:
            return self._brand_cache[slug]
        brand = self._db.scalar(select(Brand).where(Brand.slug == slug))
        if brand is None:
            brand = Brand(slug=slug, name=BRAND_NAMES.get(slug, slug.title()))
            self._db.add(brand)
            self._db.flush()
        self._brand_cache[slug] = brand
        return brand

    def get_or_create_model(self, brand: Brand, name: str) -> CarModel:
        """Args:
            brand: The model's brand (`models.brand_id` FK).
            name: Display name, e.g. `"Octavia"` - also slugified for the
                `(brand_id, slug)` natural key.

        Returns:
            The existing `CarModel` row for `(brand, slugify(name))`, or a
            newly created one.
        """
        slug = slugify(name)
        key = (brand.id, slug)
        if key in self._model_cache:
            return self._model_cache[key]
        model = self._db.scalar(
            select(CarModel).where(CarModel.brand_id == brand.id, CarModel.slug == slug)
        )
        if model is None:
            model = CarModel(brand_id=brand.id, slug=slug, name=name)
            self._db.add(model)
            self._db.flush()
        self._model_cache[key] = model
        return model

    def get_or_create_trim(self, model: CarModel, name: str) -> Trim:
        """Args:
            model: The trim's model (`trims.model_id` FK).
            name: Trim display name, e.g. `"Selection"`.

        Returns:
            The existing `Trim` row for `(model, name)`, or a newly
            created one.
        """
        key = (model.id, name)
        if key in self._trim_cache:
            return self._trim_cache[key]
        trim = self._db.scalar(select(Trim).where(Trim.model_id == model.id, Trim.name == name))
        if trim is None:
            trim = Trim(model_id=model.id, name=name)
            self._db.add(trim)
            self._db.flush()
        self._trim_cache[key] = trim
        return trim

    def get_or_create_powertrain(
        self,
        model: CarModel,
        signature: str,
        fuel_type: FuelType,
        drivetrain: Drivetrain,
        power_kw: int | None,
    ) -> Powertrain:
        """Args:
            model: The powertrain's model (`powertrains.model_id` FK).
            signature: Output of `powertrain_signature` for this variant -
                fingerprinted (see `signature_fingerprint`) and stored in
                `manufacturer_code` as this row's persisted identity.
            fuel_type: Inferred fuel type (see `infer_fuel_type`) - only
                used when actually creating a new row.
            drivetrain: Inferred drivetrain (see `infer_drivetrain`) -
                only used when actually creating a new row.
            power_kw: Extracted power in kW, or `None` (see
                `extract_power_kw`) - only used when actually creating a
                new row.

        Returns:
            The existing `Powertrain` row for `(model,
            signature_fingerprint(signature))`, or a newly created one.
            No DB-level natural-key constraint on powertrains (unlike the
            other tables) - the fingerprint in `manufacturer_code` is
            this script's own persisted identity, so a fresh process
            (empty in-memory cache) still matches the exact powertrain a
            previous run created, not just one that happens to share
            fuel_type/drivetrain/power_kw.
        """
        key = (model.id, signature)
        if key in self._powertrain_cache:
            return self._powertrain_cache[key]
        fingerprint = signature_fingerprint(signature)
        powertrain = self._db.scalar(
            select(Powertrain).where(
                Powertrain.model_id == model.id,
                Powertrain.manufacturer_code == fingerprint,
            )
        )
        if powertrain is None:
            powertrain = Powertrain(
                model_id=model.id,
                manufacturer_code=fingerprint,
                fuel_type=fuel_type,
                drivetrain=drivetrain,
                power_kw=power_kw,
            )
            self._db.add(powertrain)
            self._db.flush()
        self._powertrain_cache[key] = powertrain
        return powertrain

    def get_or_create_configuration(self, trim: Trim, powertrain: Powertrain) -> Configuration:
        """Args:
            trim: The configuration's trim.
            powertrain: The configuration's powertrain.

        Returns:
            The existing `Configuration` row for `(trim, powertrain)`
            (drivewise's own `UNIQUE(trim_id, powertrain_id)` constraint
            backs this lookup), or a newly created one.
        """
        key = (trim.id, powertrain.id)
        if key in self._configuration_cache:
            return self._configuration_cache[key]
        configuration = self._db.scalar(
            select(Configuration).where(
                Configuration.trim_id == trim.id, Configuration.powertrain_id == powertrain.id
            )
        )
        if configuration is None:
            configuration = Configuration(trim_id=trim.id, powertrain_id=powertrain.id)
            self._db.add(configuration)
            self._db.flush()
        self._configuration_cache[key] = configuration
        return configuration

    def get_or_create_source_document(
        self,
        model: CarModel,
        file_path: str,
        release_date: str | None,
        downloaded_at: str,
    ) -> SourceDocument:
        """Args:
            model: The document's model - verified 1:1 against the
                current dataset (see `run`'s docstring).
            file_path: scraper's `document.file_path` - used as this
                document's natural key, since it's unique per download.
            release_date: scraper's `document.release_date`
                (`YYYY-MM-DD`), or `None` (Kia/Toyota don't always have
                one - see `drivewise-scraper`).
            downloaded_at: scraper's `document.downloaded_at` timestamp,
                used as `effective_date`'s fallback when `release_date`
                is `None`, and always as `retrieved_at`.

        Returns:
            The existing `SourceDocument` row for `file_path`, or a newly
            created one.
        """
        if file_path in self._source_document_cache:
            return self._source_document_cache[file_path]
        source_document = self._db.scalar(
            select(SourceDocument).where(SourceDocument.file_path == file_path)
        )
        if source_document is None:
            effective_date = (
                date.fromisoformat(release_date)
                if release_date
                else datetime.fromisoformat(downloaded_at).date()
            )
            source_document = SourceDocument(
                model_id=model.id,
                file_path=file_path,
                document_type=DocumentType.price_list,
                market=MARKET,
                locale=LOCALE,
                effective_date=effective_date,
                retrieved_at=datetime.fromisoformat(downloaded_at).replace(tzinfo=timezone.utc),
            )
            self._db.add(source_document)
            self._db.flush()
        self._source_document_cache[file_path] = source_document
        return source_document

    def upsert_price(
        self,
        configuration: Configuration,
        source_document: SourceDocument,
        amount: float,
        currency: str,
        valid_from: str,
    ) -> None:
        """Inserts a new current-price row for `configuration`, closing
        out the previous one - unless the current row already matches
        (no-op) or `valid_from` would rewrite history backwards (also a
        no-op). Updates `self.stats.prices_inserted`/`prices_unchanged`.

        Args:
            configuration: The configuration this price is for.
            source_document: The document this price was read from.
            amount: New price amount (used for both `list_price` and
                `price_incl_vat` - scraper doesn't distinguish them).
            currency: New price's currency.
            valid_from: New price's effective date (`YYYY-MM-DD`).
        """
        valid_from_date = date.fromisoformat(valid_from)
        current = self._db.scalar(
            select(Price).where(
                Price.configuration_id == configuration.id,
                Price.market == MARKET,
                Price.valid_to.is_(None),
            )
        )
        if current is not None:
            if (
                float(current.price_incl_vat) == amount
                and current.currency == currency
                and current.valid_from == valid_from_date
            ):
                self.stats.prices_unchanged += 1
                return
            if valid_from_date <= current.valid_from:
                # Stale/out-of-order data (e.g. reprocessing an older
                # document) - never rewrite history backwards.
                self.stats.prices_unchanged += 1
                return
            current.valid_to = valid_from_date

        self._db.add(
            Price(
                configuration_id=configuration.id,
                source_document_id=source_document.id,
                market=MARKET,
                currency=currency,
                list_price=amount,
                price_incl_vat=amount,
                valid_from=valid_from_date,
                valid_to=None,
                scraped_at=datetime.now(timezone.utc),
            )
        )
        # SessionLocal is autoflush=False (see app/db/session.py) - flush
        # now so the next call's `current = self._db.scalar(select(Price)
        # ...)` above actually sees this row. Without it, two scraper
        # variants that collapse into the same configuration in the same
        # run (the source PDFs do contain exact duplicate rows - e.g.
        # Škoda Scala's "Top Selection 1,0 TSI/85 kW" appears twice) would
        # both pass the "no current price yet" branch and violate the
        # partial unique index on the second insert.
        self._db.flush()
        self.stats.prices_inserted += 1

    def run(self) -> ImportStats:
        """Imports every document/variant/price from `scraper_con` into
        `db`, via the `get_or_create_*`/`upsert_price` methods above.
        Does not commit or roll back - the caller (see `main`) owns the
        transaction boundary.

        Returns:
            `self.stats`, fully populated (also available as `self.stats`
            immediately after this returns, for callers that want it
            without capturing the return value).
        """
        self.stats.equipment_skipped = self._scraper_con.execute(
            "SELECT COUNT(*) FROM equipment_assignment"
        ).fetchone()[0]

        documents = self._scraper_con.execute(
            "SELECT id, source_brand, file_path, release_date, downloaded_at FROM document"
        ).fetchall()

        for doc_id, source_brand, file_path, release_date, downloaded_at in documents:
            variants = self._scraper_con.execute(
                "SELECT id, model, trim, powertrain, variant_name FROM variant WHERE document_id = ?",
                (doc_id,),
            ).fetchall()
            if not variants:
                continue

            brand = self.get_or_create_brand(source_brand)
            # Verified against the current dataset: every scraper document
            # covers exactly one model (see the ETL design notes this script
            # was built from) - all variants under a document share the same
            # `model` value, so the first one determines it.
            model = self.get_or_create_model(brand, variants[0][1])
            source_document = self.get_or_create_source_document(
                model, file_path, release_date, downloaded_at
            )

            for variant_id, _model_name, trim_name, scraper_powertrain, variant_name in variants:
                trim = self.get_or_create_trim(model, trim_name)

                fuel_type = infer_fuel_type(scraper_powertrain, variant_name)
                drivetrain = infer_drivetrain(variant_name)
                power_kw = extract_power_kw(variant_name)
                signature = powertrain_signature(variant_name, trim_name)
                powertrain = self.get_or_create_powertrain(
                    model, signature, fuel_type, drivetrain, power_kw
                )
                configuration = self.get_or_create_configuration(trim, powertrain)

                price_row = self._scraper_con.execute(
                    "SELECT price, currency, valid_from FROM price_history "
                    "WHERE variant_id = ? ORDER BY valid_from DESC LIMIT 1",
                    (variant_id,),
                ).fetchone()
                if price_row is not None:
                    amount, currency, valid_from = price_row
                    self.upsert_price(configuration, source_document, amount, currency, valid_from)

        self.stats.brands = len(self._brand_cache)
        self.stats.models = len(self._model_cache)
        self.stats.trims = len(self._trim_cache)
        self.stats.powertrains = len(self._powertrain_cache)
        self.stats.configurations = len(self._configuration_cache)
        self.stats.source_documents = len(self._source_document_cache)
        return self.stats


def main() -> None:
    """CLI entry point: parses `--dry-run`, runs one `ScraperDataImporter`
    pass, commits (or rolls back for `--dry-run`), and prints the summary.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run", action="store_true", help="Run the import but roll back instead of committing."
    )
    args = parser.parse_args()

    if not SCRAPER_DB_PATH.exists():
        raise SystemExit(f"scraper DB not found at {SCRAPER_DB_PATH} - run the scraper first.")

    scraper_con = sqlite3.connect(SCRAPER_DB_PATH)
    db = SessionLocal()
    try:
        importer = ScraperDataImporter(db, scraper_con)
        stats = importer.run()
        if args.dry_run:
            db.rollback()
        else:
            db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
        scraper_con.close()

    print(f"{'[DRY RUN] ' if args.dry_run else ''}Import summary:")
    print(f"  brands: {stats.brands}, models: {stats.models}, trims: {stats.trims}")
    print(f"  powertrains: {stats.powertrains}, configurations: {stats.configurations}")
    print(f"  source_documents: {stats.source_documents}")
    print(f"  prices: {stats.prices_inserted} inserted, {stats.prices_unchanged} already up to date")
    print(
        f"  equipment_assignment rows skipped (no surcharge data to import): {stats.equipment_skipped}"
    )


if __name__ == "__main__":
    main()
