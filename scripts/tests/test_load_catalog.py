"""Tests for scripts/load_catalog.py - the catalog copy between two SQLite
files (the Postgres-only sequence reset isn't exercised here)."""

import importlib.util
import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest
from sqlalchemy import Engine, create_engine, func, select, text
from sqlalchemy.orm import Session

_SPEC = importlib.util.spec_from_file_location(
    "load_catalog_script", Path(__file__).resolve().parents[1] / "load_catalog.py"
)
load_catalog = importlib.util.module_from_spec(_SPEC)
# Registered before running it: @dataclass looks its module up there.
sys.modules[_SPEC.name] = load_catalog
_SPEC.loader.exec_module(load_catalog)

from app.db.base import Base  # noqa: E402  (importable once the script put backend/ on sys.path)
from app.db.seed import seed_demo_data  # noqa: E402
from app.models import User  # noqa: E402


def _database(path: Path, revision: str | None = "head1") -> Engine:
    engine = create_engine(f"sqlite:///{path.as_posix()}")
    Base.metadata.create_all(engine)
    if revision:
        with engine.begin() as conn:
            conn.execute(text("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL)"))
            conn.execute(text("INSERT INTO alembic_version VALUES (:r)"), {"r": revision})
    return engine


@pytest.fixture()
def source(tmp_path: Path) -> Engine:
    engine = _database(tmp_path / "source.db")
    with Session(engine) as session:
        seed_demo_data(session)
        session.commit()
    return engine


def _counts(engine: Engine) -> dict[str, int]:
    with engine.connect() as conn:
        return {
            t.name: conn.execute(select(func.count()).select_from(t)).scalar() for t in load_catalog.catalog_tables()
        }


def test_catalog_tables_come_parents_first() -> None:
    names = [t.name for t in load_catalog.catalog_tables()]
    assert set(names) == load_catalog.CATALOG_TABLES
    assert names.index("brands") < names.index("models") < names.index("configurations") < names.index("prices")


def test_copies_every_catalog_row_with_its_id(source: Engine, tmp_path: Path) -> None:
    target = _database(tmp_path / "target.db")
    copied = load_catalog.CatalogLoader(source, target, batch_size=3).run()
    assert copied == _counts(source) == _counts(target)
    assert copied["configurations"] == 4
    with source.connect() as s, target.connect() as t:
        query = text("SELECT id, name FROM models ORDER BY id")
        assert s.execute(query).all() == t.execute(query).all()


def test_user_tables_are_left_alone(source: Engine, tmp_path: Path) -> None:
    target = _database(tmp_path / "target.db")
    with Session(source) as session:
        session.add(User(email="someone@example.cz", created_at=datetime.now(UTC)))
        session.commit()
    load_catalog.CatalogLoader(source, target).run()
    with target.connect() as conn:
        assert conn.execute(select(func.count()).select_from(User.__table__)).scalar() == 0


def test_dry_run_writes_nothing(source: Engine, tmp_path: Path) -> None:
    target = _database(tmp_path / "target.db")
    copied = load_catalog.CatalogLoader(source, target).run(dry_run=True)
    assert copied["models"] == 2
    assert set(_counts(target).values()) == {0}


def test_refuses_a_target_that_already_has_a_catalog(source: Engine, tmp_path: Path) -> None:
    target = _database(tmp_path / "target.db")
    load_catalog.CatalogLoader(source, target).run()
    with pytest.raises(load_catalog.LoadError, match="not empty"):
        load_catalog.CatalogLoader(source, target).run()


def test_refuses_different_schema_versions(source: Engine, tmp_path: Path) -> None:
    target = _database(tmp_path / "target.db", revision="older")
    with pytest.raises(load_catalog.LoadError, match="schema versions differ"):
        load_catalog.CatalogLoader(source, target).run()


def test_refuses_an_empty_source(tmp_path: Path) -> None:
    empty, target = _database(tmp_path / "empty.db"), _database(tmp_path / "target.db")
    with pytest.raises(load_catalog.LoadError, match="source catalog is empty"):
        load_catalog.CatalogLoader(empty, target).run()


def test_describe_hides_the_password() -> None:
    described = load_catalog.describe("postgresql+psycopg://user:secret@ep-x.neon.tech/neondb?sslmode=require")
    assert "secret" not in described
    assert described == "postgresql ep-x.neon.tech"


def test_main_requires_a_target(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TARGET_DATABASE_URL", raising=False)
    assert load_catalog.main([]) == 2
