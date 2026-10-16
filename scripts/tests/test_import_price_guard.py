"""Tests for scripts/import_scraper_data.py's guard against prices that
can't fit the NUMERIC(12, 2) price columns (parse errors such as two
adjacent prices read as one number)."""

import importlib.util
import sqlite3
import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

_SPEC = importlib.util.spec_from_file_location(
    "import_scraper_data_script", Path(__file__).resolve().parents[1] / "import_scraper_data.py"
)
importer_module = importlib.util.module_from_spec(_SPEC)
# Registered before running it: @dataclass looks its module up there.
sys.modules[_SPEC.name] = importer_module
_SPEC.loader.exec_module(importer_module)

from app.db.base import Base  # noqa: E402  (importable once the script put backend/ on sys.path)
from app.db.seed import seed_demo_data  # noqa: E402
from app.models import Configuration, Price, SourceDocument  # noqa: E402


@pytest.fixture()
def importer():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        seed_demo_data(session)
        yield importer_module.ScraperDataImporter(session, sqlite3.connect(":memory:")), session


def test_out_of_range_price_is_skipped_with_a_warning(importer) -> None:
    job, session = importer
    configuration = session.scalars(select(Configuration)).first()
    document = session.scalars(select(SourceDocument)).first()
    before = session.scalar(select(Price.price_incl_vat).where(Price.configuration_id == configuration.id))

    job.upsert_price(configuration, document, 780500845500.0, "CZK", "2030-01-01")

    assert job.stats.prices_skipped == 1
    assert job.stats.prices_inserted == 0
    assert "780,500,845,500 CZK" in job.stats.warnings[0]
    current = session.scalars(
        select(Price).where(Price.configuration_id == configuration.id, Price.valid_to.is_(None))
    ).one()
    assert current.price_incl_vat == before


def test_normal_price_still_imports(importer) -> None:
    job, session = importer
    configuration = session.scalars(select(Configuration)).first()
    document = session.scalars(select(SourceDocument)).first()

    job.upsert_price(configuration, document, 845500.0, "CZK", "2030-01-01")

    assert job.stats.prices_inserted == 1
    assert job.stats.prices_skipped == 0
