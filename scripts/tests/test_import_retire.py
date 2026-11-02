"""Tests for scripts/import_scraper_data.py's retiring of variants that a
newer version of the same price list (same scraper `document_url`) no
longer contains - the class of stale data behind the Ford Puma "ST-Line X
BlueCruise Edition" row an earlier parser version produced."""

import importlib.util
import sqlite3
import sys
from datetime import date
from pathlib import Path

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

_SPEC = importlib.util.spec_from_file_location(
    "import_scraper_data_retire", Path(__file__).resolve().parents[1] / "import_scraper_data.py"
)
importer_module = importlib.util.module_from_spec(_SPEC)
# Registered before running it: @dataclass looks its module up there.
sys.modules[_SPEC.name] = importer_module
_SPEC.loader.exec_module(importer_module)

from app.db.base import Base  # noqa: E402  (importable once the script put backend/ on sys.path)
from app.models import Configuration, Price, Trim  # noqa: E402

PUMA = "https://ford.example/PL-Puma.pdf"
KUGA = "https://ford.example/PL-Kuga.pdf"


def _scraper_db(documents: list[tuple[int, str, str, list[tuple[str, str, float]]]]) -> sqlite3.Connection:
    """Builds an in-memory scraper.db: each document is (id, url, date,
    [(model, trim, price), ...]); every variant shares one engine."""
    con = sqlite3.connect(":memory:")
    con.executescript(
        """
        CREATE TABLE document (id INTEGER PRIMARY KEY, source_brand TEXT, document_url TEXT, file_path TEXT,
                               release_date TEXT, downloaded_at TEXT);
        CREATE TABLE variant (id INTEGER PRIMARY KEY, document_id INTEGER, model TEXT, trim TEXT,
                              powertrain TEXT, variant_name TEXT);
        CREATE TABLE price_history (id INTEGER PRIMARY KEY, variant_id INTEGER, price REAL, currency TEXT,
                                    valid_from TEXT);
        CREATE TABLE equipment (id INTEGER PRIMARY KEY, canonical_name TEXT);
        CREATE TABLE equipment_assignment (id INTEGER PRIMARY KEY, variant_id INTEGER, equipment_id INTEGER,
                                           availability TEXT, surcharge_amount REAL, currency TEXT);
        """
    )
    for doc_id, url, day, variants in documents:
        con.execute(
            "INSERT INTO document VALUES (?, 'ford', ?, ?, ?, ?)",
            (doc_id, url, f"/storage/ford/{doc_id}.pdf", day, f"{day}T10:00:00"),
        )
        for model, trim, price in variants:
            cursor = con.execute(
                "INSERT INTO variant (document_id, model, trim, powertrain, variant_name) VALUES (?, ?, ?, 'ICE', ?)",
                (doc_id, model, trim, f"{model} {trim} 1.0 EcoBoost 92 kW"),
            )
            con.execute(
                "INSERT INTO price_history (variant_id, price, currency, valid_from) VALUES (?, ?, 'CZK', ?)",
                (cursor.lastrowid, price, day),
            )
    return con


@pytest.fixture()
def session():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        yield db


def _current_prices(session: Session) -> dict[str, float]:
    rows = session.execute(
        select(Trim.name, Price.price_incl_vat)
        .join(Configuration, Configuration.trim_id == Trim.id)
        .join(Price, Price.configuration_id == Configuration.id)
        .where(Price.valid_to.is_(None))
    ).all()
    return {trim: float(price) for trim, price in rows}


def test_variant_dropped_from_newer_version_is_retired(session: Session) -> None:
    scraper = _scraper_db(
        [
            (1, PUMA, "2026-10-01", [("Puma", "ST-Line X", 725_500.0), ("Puma", "ST-Line X BlueCruise", 780_500.0)]),
            (2, PUMA, "2026-11-01", [("Puma", "ST-Line X", 725_500.0), ("Puma", "BlueCruise Edition", 845_500.0)]),
        ]
    )
    stats = importer_module.ScraperDataImporter(session, scraper).run()

    assert stats.prices_retired == 1
    assert _current_prices(session) == {"ST-Line X": 725_500.0, "BlueCruise Edition": 845_500.0}
    retired = session.scalars(
        select(Price).join(Configuration).join(Trim).where(Trim.name == "ST-Line X BlueCruise")
    ).one()
    assert retired.valid_to == date(2026, 11, 1)  # closed, not deleted


def test_rerun_does_not_bring_a_retired_variant_back(session: Session) -> None:
    scraper = _scraper_db(
        [
            (1, PUMA, "2026-10-01", [("Puma", "Titanium", 629_500.0), ("Puma", "Old Edition", 700_000.0)]),
            (2, PUMA, "2026-11-01", [("Puma", "Titanium", 629_500.0)]),
        ]
    )
    importer_module.ScraperDataImporter(session, scraper).run()

    second = importer_module.ScraperDataImporter(session, scraper).run()

    assert second.prices_inserted == 0
    assert second.prices_retired == 0
    assert _current_prices(session) == {"Titanium": 629_500.0}


def test_variant_priced_by_another_price_list_is_left_alone(session: Session) -> None:
    # "Shared" ends up priced by the Kuga list (newer), so the Puma list
    # dropping it later must not close that price.
    scraper = _scraper_db(
        [
            (1, PUMA, "2026-10-01", [("Puma", "Titanium", 629_500.0), ("Puma", "Shared", 700_000.0)]),
            (2, KUGA, "2026-10-15", [("Puma", "Shared", 710_000.0)]),
            (3, PUMA, "2026-11-01", [("Puma", "Titanium", 629_500.0)]),
        ]
    )
    stats = importer_module.ScraperDataImporter(session, scraper).run()

    assert stats.prices_retired == 0
    assert _current_prices(session) == {"Titanium": 629_500.0, "Shared": 710_000.0}


def test_failed_parse_with_no_variants_retires_nothing(session: Session) -> None:
    scraper = _scraper_db(
        [
            (1, PUMA, "2026-10-01", [("Puma", "Titanium", 629_500.0)]),
            (2, PUMA, "2026-11-01", []),
        ]
    )
    stats = importer_module.ScraperDataImporter(session, scraper).run()

    assert stats.prices_retired == 0
    assert _current_prices(session) == {"Titanium": 629_500.0}


def test_variant_that_returns_in_a_later_version_is_priced_again(session: Session) -> None:
    scraper = _scraper_db(
        [
            (1, PUMA, "2026-09-01", [("Puma", "Titanium", 629_500.0), ("Puma", "ST-Line", 673_500.0)]),
            (2, PUMA, "2026-10-01", [("Puma", "Titanium", 629_500.0)]),
            (3, PUMA, "2026-11-01", [("Puma", "Titanium", 629_500.0), ("Puma", "ST-Line", 679_500.0)]),
        ]
    )
    importer_module.ScraperDataImporter(session, scraper).run()

    assert _current_prices(session) == {"Titanium": 629_500.0, "ST-Line": 679_500.0}
