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
    normalized = unicodedata.normalize("NFKD", text)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_text).strip("-").lower()
    return slug or "x"


def infer_fuel_type(scraper_powertrain: str, variant_name: str) -> FuelType:
    if scraper_powertrain in _SCRAPER_TO_FUEL_TYPE:
        return _SCRAPER_TO_FUEL_TYPE[scraper_powertrain]
    # scraper_powertrain == "ICE": split into petrol/diesel from the name.
    return FuelType.diesel if _DIESEL_RE.search(variant_name) else FuelType.petrol


def infer_drivetrain(variant_name: str) -> Drivetrain:
    # RWD isn't distinguishable from the naming these brands use for these
    # segments (no rear-drive models in this data) - default to fwd, the
    # overwhelming majority, rather than guess at rwd.
    return Drivetrain.awd if _AWD_RE.search(variant_name) else Drivetrain.fwd


def extract_power_kw(text: str) -> int | None:
    m = _KW_RE.search(text)
    return int(m.group(1)) if m else None


def powertrain_signature(variant_name: str, trim: str) -> str:
    """A stable per-model dedup key for 'the same engine' across trims -
    the variant name with the (already separately tracked) trim name
    removed, since scraper's variant_name = model + trim + engine spec in
    an order that differs by brand (trim is sometimes in the middle,
    sometimes at the end) - see this script's module docstring.
    """
    remainder = variant_name.replace(trim, "") if trim else variant_name
    return re.sub(r"\s+", " ", remainder).strip().lower()


def signature_fingerprint(signature: str) -> str:
    """Short, deterministic stand-in for `signature` that fits in
    Powertrain.manufacturer_code (String(32)) - used as the persisted
    identity for matching 'the same engine' across separate runs of this
    script (see get_or_create_powertrain). (fuel_type, drivetrain,
    power_kw) alone isn't a reliable identity: two genuinely different
    engines within a model can share all three (e.g. two similarly-tuned
    petrol FWD variants), so a rerun without this would risk silently
    merging or splitting powertrains rather than matching the exact one
    this script created originally.
    """
    return "scr:" + hashlib.sha256(signature.encode("utf-8")).hexdigest()[:24]


@dataclass
class ImportStats:
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


def get_or_create_brand(db: Session, cache: dict[str, Brand], slug: str) -> Brand:
    if slug in cache:
        return cache[slug]
    brand = db.scalar(select(Brand).where(Brand.slug == slug))
    if brand is None:
        brand = Brand(slug=slug, name=BRAND_NAMES.get(slug, slug.title()))
        db.add(brand)
        db.flush()
    cache[slug] = brand
    return brand


def get_or_create_model(
    db: Session, cache: dict[tuple[int, str], CarModel], brand: Brand, name: str
) -> CarModel:
    slug = slugify(name)
    key = (brand.id, slug)
    if key in cache:
        return cache[key]
    model = db.scalar(
        select(CarModel).where(CarModel.brand_id == brand.id, CarModel.slug == slug)
    )
    if model is None:
        model = CarModel(brand_id=brand.id, slug=slug, name=name)
        db.add(model)
        db.flush()
    cache[key] = model
    return model


def get_or_create_trim(
    db: Session, cache: dict[tuple[int, str], Trim], model: CarModel, name: str
) -> Trim:
    key = (model.id, name)
    if key in cache:
        return cache[key]
    trim = db.scalar(select(Trim).where(Trim.model_id == model.id, Trim.name == name))
    if trim is None:
        trim = Trim(model_id=model.id, name=name)
        db.add(trim)
        db.flush()
    cache[key] = trim
    return trim


def get_or_create_powertrain(
    db: Session,
    cache: dict[tuple[int, str], Powertrain],
    model: CarModel,
    signature: str,
    fuel_type: FuelType,
    drivetrain: Drivetrain,
    power_kw: int | None,
) -> Powertrain:
    key = (model.id, signature)
    if key in cache:
        return cache[key]
    # No DB-level natural-key constraint on powertrains (unlike the other
    # tables) - manufacturer_code holds this script's own fingerprint of
    # `signature` (see signature_fingerprint) so a fresh process (empty
    # in-memory cache) still matches the exact powertrain a previous run
    # created, not just one that happens to share fuel_type/drivetrain/
    # power_kw.
    fingerprint = signature_fingerprint(signature)
    powertrain = db.scalar(
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
        db.add(powertrain)
        db.flush()
    cache[key] = powertrain
    return powertrain


def get_or_create_configuration(
    db: Session,
    cache: dict[tuple[int, int], Configuration],
    trim: Trim,
    powertrain: Powertrain,
) -> Configuration:
    key = (trim.id, powertrain.id)
    if key in cache:
        return cache[key]
    configuration = db.scalar(
        select(Configuration).where(
            Configuration.trim_id == trim.id, Configuration.powertrain_id == powertrain.id
        )
    )
    if configuration is None:
        configuration = Configuration(trim_id=trim.id, powertrain_id=powertrain.id)
        db.add(configuration)
        db.flush()
    cache[key] = configuration
    return configuration


def get_or_create_source_document(
    db: Session,
    cache: dict[str, SourceDocument],
    model: CarModel,
    file_path: str,
    release_date: str | None,
    downloaded_at: str,
) -> SourceDocument:
    if file_path in cache:
        return cache[file_path]
    source_document = db.scalar(
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
        db.add(source_document)
        db.flush()
    cache[file_path] = source_document
    return source_document


def upsert_price(
    db: Session,
    configuration: Configuration,
    source_document: SourceDocument,
    amount: float,
    currency: str,
    valid_from: str,
    stats: ImportStats,
) -> None:
    valid_from_date = date.fromisoformat(valid_from)
    current = db.scalar(
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
            stats.prices_unchanged += 1
            return
        if valid_from_date <= current.valid_from:
            # Stale/out-of-order data (e.g. reprocessing an older
            # document) - never rewrite history backwards.
            stats.prices_unchanged += 1
            return
        current.valid_to = valid_from_date

    db.add(
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
    # SessionLocal is autoflush=False (see app/db/session.py) - flush now
    # so the next call's `current = db.scalar(select(Price)...)` above
    # actually sees this row. Without it, two scraper variants that
    # collapse into the same configuration in the same run (the source
    # PDFs do contain exact duplicate rows - e.g. Škoda Scala's "Top
    # Selection 1,0 TSI/85 kW" appears twice) would both pass the "no
    # current price yet" branch and violate the partial unique index on
    # the second insert.
    db.flush()
    stats.prices_inserted += 1


def run_import(db: Session, scraper_con: sqlite3.Connection, stats: ImportStats) -> None:
    brand_cache: dict[str, Brand] = {}
    model_cache: dict[tuple[int, str], CarModel] = {}
    trim_cache: dict[tuple[int, str], Trim] = {}
    powertrain_cache: dict[tuple[int, str], Powertrain] = {}
    configuration_cache: dict[tuple[int, int], Configuration] = {}
    source_document_cache: dict[str, SourceDocument] = {}

    stats.equipment_skipped = scraper_con.execute(
        "SELECT COUNT(*) FROM equipment_assignment"
    ).fetchone()[0]

    documents = scraper_con.execute(
        "SELECT id, source_brand, file_path, release_date, downloaded_at FROM document"
    ).fetchall()

    for doc_id, source_brand, file_path, release_date, downloaded_at in documents:
        variants = scraper_con.execute(
            "SELECT id, model, trim, powertrain, variant_name FROM variant WHERE document_id = ?",
            (doc_id,),
        ).fetchall()
        if not variants:
            continue

        brand = get_or_create_brand(db, brand_cache, source_brand)
        # Verified against the current dataset: every scraper document
        # covers exactly one model (see the ETL design notes this script
        # was built from) - all variants under a document share the same
        # `model` value, so the first one determines it.
        model = get_or_create_model(db, model_cache, brand, variants[0][1])
        source_document = get_or_create_source_document(
            db, source_document_cache, model, file_path, release_date, downloaded_at
        )

        for variant_id, _model_name, trim_name, scraper_powertrain, variant_name in variants:
            trim = get_or_create_trim(db, trim_cache, model, trim_name)

            fuel_type = infer_fuel_type(scraper_powertrain, variant_name)
            drivetrain = infer_drivetrain(variant_name)
            power_kw = extract_power_kw(variant_name)
            signature = powertrain_signature(variant_name, trim_name)
            powertrain = get_or_create_powertrain(
                db, powertrain_cache, model, signature, fuel_type, drivetrain, power_kw
            )
            configuration = get_or_create_configuration(db, configuration_cache, trim, powertrain)

            price_row = scraper_con.execute(
                "SELECT price, currency, valid_from FROM price_history "
                "WHERE variant_id = ? ORDER BY valid_from DESC LIMIT 1",
                (variant_id,),
            ).fetchone()
            if price_row is not None:
                amount, currency, valid_from = price_row
                upsert_price(db, configuration, source_document, amount, currency, valid_from, stats)

    stats.brands = len(brand_cache)
    stats.models = len(model_cache)
    stats.trims = len(trim_cache)
    stats.powertrains = len(powertrain_cache)
    stats.configurations = len(configuration_cache)
    stats.source_documents = len(source_document_cache)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run", action="store_true", help="Run the import but roll back instead of committing."
    )
    args = parser.parse_args()

    if not SCRAPER_DB_PATH.exists():
        raise SystemExit(f"scraper DB not found at {SCRAPER_DB_PATH} - run the scraper first.")

    scraper_con = sqlite3.connect(SCRAPER_DB_PATH)
    db = SessionLocal()
    stats = ImportStats()
    try:
        run_import(db, scraper_con, stats)
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
