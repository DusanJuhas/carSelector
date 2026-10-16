#!/usr/bin/env python3
"""Loads the vehicle catalog into a remote, empty Postgres database (Neon)
by building it locally first and then bulk-copying the rows.

Why not just run scripts/import_scraper_data.py against the remote
database: that import resolves every brand/model/trim/... by natural key
and inserts row by row - about 170,000 queries for the current
storage/scraper.db. Locally on SQLite that takes a minute; over a 60 ms
round trip to Neon it takes hours. This script runs the same import into a
throwaway local SQLite file and then copies the finished catalog tables in
batches of a few thousand rows (a few hundred round trips in total).

Steps:
1. build: `alembic upgrade head` + `scripts/import_scraper_data.py` into a
   temporary SQLite file (skipped with --source, which uses an existing
   SQLite database instead - only its catalog tables are read);
2. migrate: `alembic upgrade head` on the target;
3. check: both databases are at the same Alembic revision, and every
   catalog table in the target is empty - the copy keeps the source's ids,
   so it is only for the first load. Later catalog updates go through
   scripts/import_scraper_data.py (natural-key lookups keep the ids that
   users' likes and comparison stats point at);
4. copy: all catalog tables in one transaction, in foreign-key order, then
   (on Postgres) moves each id sequence past the copied ids so the app's
   own later inserts don't collide.

Only catalog tables are touched (CATALOG_TABLES) - users, articles,
feedback, shared links etc. are never read or written.

Configuration:

    TARGET_DATABASE_URL   connection string of the target, e.g. Neon's
                          direct one. postgres:// and postgresql:// work
                          (normalized like the app's DATABASE_URL).

Usage (from the repo root):

    python scripts/load_catalog.py               build, migrate, check, copy
    python scripts/load_catalog.py --dry-run     same, but roll the copy back
    python scripts/load_catalog.py --source storage/drivewise.db
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = REPO_ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import Connection, Engine, Table, create_engine, func, inspect, select, text  # noqa: E402
from sqlalchemy.engine import make_url  # noqa: E402

import app.models  # noqa: E402, F401  - registers every table on Base.metadata
from app.core.config import normalize_database_url  # noqa: E402
from app.db.base import Base  # noqa: E402

# The catalog as scripts/import_scraper_data.py and app/db/seed.py write
# it. Everything else in the schema is user data and stays untouched.
CATALOG_TABLES = frozenset(
    {
        "brands",
        "models",
        "trims",
        "powertrains",
        "source_documents",
        "colors",
        "option_items",
        "configurations",
        "configuration_colors",
        "option_availability",
        "prices",
    }
)
BATCH_SIZE = 2000


def catalog_tables() -> list[Table]:
    """Returns:
    The catalog tables in foreign-key order (parents before children).
    """
    return [table for table in Base.metadata.sorted_tables if table.name in CATALOG_TABLES]


def describe(url: str) -> str:
    """Args:
        url: A database URL.

    Returns:
        Dialect and host/file only - never the password.
    """
    parsed = make_url(url)
    return f"{parsed.get_backend_name()} {parsed.host or parsed.database}"


class LoadError(Exception):
    """A step failed or a safety check refused the load."""


@dataclass
class CatalogLoader:
    """Copies the catalog tables from a source to an empty target database.

    Attributes:
        source: Engine of the fully imported (local) database.
        target: Engine of the database to fill.
        batch_size: Rows per INSERT batch.
    """

    source: Engine
    target: Engine
    batch_size: int = BATCH_SIZE

    @staticmethod
    def revision(conn: Connection) -> str | None:
        """Args:
            conn: An open connection.

        Returns:
            The Alembic revision the database is at, or None without one.
        """
        if not inspect(conn).has_table("alembic_version"):
            return None
        return conn.execute(text("SELECT version_num FROM alembic_version")).scalar()

    def check(self, src: Connection, dst: Connection) -> dict[str, int]:
        """Refuses unless both schemas match and the target catalog is empty.

        Args:
            src: Connection to the source.
            dst: Connection to the target.

        Returns:
            Row counts per catalog table in the source.

        Raises:
            LoadError: Revisions differ, or the target already has catalog rows.
        """
        src_rev, dst_rev = self.revision(src), self.revision(dst)
        if src_rev != dst_rev:
            raise LoadError(f"schema versions differ: source {src_rev}, target {dst_rev} - run alembic upgrade head")
        filled = {
            t.name: n for t in catalog_tables() if (n := dst.execute(select(func.count()).select_from(t)).scalar())
        }
        if filled:
            raise LoadError(
                f"target catalog is not empty ({filled}) - this copy is only for the first load; "
                "update an existing catalog with scripts/import_scraper_data.py"
            )
        counts = {t.name: src.execute(select(func.count()).select_from(t)).scalar() for t in catalog_tables()}
        if not counts.get("configurations"):
            raise LoadError("source catalog is empty - nothing to copy")
        return counts

    def copy(self, src: Connection, dst: Connection) -> dict[str, int]:
        """Copies every catalog table, keeping ids, inside the caller's
        target transaction.

        Args:
            src: Connection to the source.
            dst: Connection to the target (in a transaction).

        Returns:
            Rows copied per table.
        """
        copied: dict[str, int] = {}
        for table in catalog_tables():
            rows = src.execute(select(table).order_by(*table.primary_key.columns)).mappings()
            total = 0
            for batch in rows.partitions(self.batch_size):
                dst.execute(table.insert(), [dict(row) for row in batch])
                total += len(batch)
            copied[table.name] = total
        if dst.dialect.name == "postgresql":
            self.reset_sequences(dst)
        return copied

    @staticmethod
    def reset_sequences(dst: Connection) -> None:
        """Moves each catalog table's id sequence past the copied ids -
        explicit-id inserts don't advance it, so the next app insert would
        otherwise reuse id 1.

        Args:
            dst: Connection to a Postgres target.
        """
        for table in catalog_tables():
            sequence = dst.execute(text("SELECT pg_get_serial_sequence(:t, 'id')"), {"t": table.name}).scalar()
            if sequence:
                dst.execute(
                    text(f"SELECT setval(:s, COALESCE((SELECT MAX(id) FROM {table.name}), 0) + 1, false)"),
                    {"s": sequence},
                )

    def run(self, dry_run: bool = False) -> dict[str, int]:
        """Checks, then copies in one transaction (rolled back for a dry run)
        and verifies the target's counts against the source's.

        Args:
            dry_run: Roll back instead of committing.

        Returns:
            Rows copied per table.

        Raises:
            LoadError: A check failed or the counts don't match.
        """
        with self.source.connect() as src, self.target.connect() as dst:
            # The check runs inside the copy's transaction, so nothing can
            # fill the target between "it's empty" and the inserts.
            transaction = dst.begin()
            try:
                expected = self.check(src, dst)
                copied = self.copy(src, dst)
                if copied != expected:
                    raise LoadError(f"row counts differ after copy: expected {expected}, copied {copied}")
                if dry_run:
                    transaction.rollback()
                else:
                    transaction.commit()
            except BaseException:
                if transaction.is_active:
                    transaction.rollback()
                raise
        return copied


def run_step(description: str, cmd: list[str], cwd: Path, database_url: str) -> None:
    """Runs a repo command with DATABASE_URL pointed at a given database.

    Args:
        description: What the step does, for the progress output.
        cmd: The command.
        cwd: Working directory.
        database_url: Value for DATABASE_URL in the child's environment.

    Raises:
        LoadError: The command failed (its output is shown).
    """
    print(f"- {description} ...", flush=True)
    started = time.perf_counter()
    result = subprocess.run(
        cmd, cwd=cwd, env={**os.environ, "DATABASE_URL": database_url}, capture_output=True, text=True
    )
    if result.returncode != 0:
        output = (result.stdout + result.stderr).replace(database_url, "<DATABASE_URL>")
        raise LoadError(f"{description} failed:\n{output[-3000:]}")
    print(f"  done in {time.perf_counter() - started:.0f} s", flush=True)
    # The import's summary flags rows it had to skip - pass those on.
    for line in result.stdout.splitlines():
        if "WARNING" in line or "skipped" in line:
            print(f"  {line.strip()}", flush=True)


def main(argv: list[str] | None = None) -> int:
    """CLI entry point.

    Args:
        argv: Arguments (default: `sys.argv[1:]`).

    Returns:
        0 on success, 1 if a step failed or a check refused, 2 without
        TARGET_DATABASE_URL.
    """
    parser = argparse.ArgumentParser(description="Load the catalog into an empty remote database.")
    parser.add_argument("--source", type=Path, help="existing SQLite database to copy from (skips the local build)")
    parser.add_argument("--dry-run", action="store_true", help="copy, verify, then roll back")
    args = parser.parse_args(argv)

    raw_target = os.getenv("TARGET_DATABASE_URL")
    if not raw_target:
        print("TARGET_DATABASE_URL is not set.", file=sys.stderr)
        return 2
    target_url = normalize_database_url(raw_target)
    python = sys.executable

    with tempfile.TemporaryDirectory(prefix="drivewise-catalog-", ignore_cleanup_errors=True) as tmp:
        try:
            if args.source:
                source_url = f"sqlite:///{args.source.resolve().as_posix()}"
            else:
                source_url = f"sqlite:///{(Path(tmp) / 'catalog.db').as_posix()}"
                run_step(
                    "local schema (alembic upgrade head)",
                    [python, "-m", "alembic", "upgrade", "head"],
                    BACKEND_DIR,
                    source_url,
                )
                run_step(
                    "local import (import_scraper_data.py)",
                    [python, "scripts/import_scraper_data.py"],
                    REPO_ROOT,
                    source_url,
                )
            run_step(
                f"target schema on {describe(target_url)} (alembic upgrade head)",
                [python, "-m", "alembic", "upgrade", "head"],
                BACKEND_DIR,
                target_url,
            )
            print(f"- copying catalog tables{' (dry run)' if args.dry_run else ''} ...", flush=True)
            started = time.perf_counter()
            source, target = create_engine(source_url), create_engine(target_url)
            try:
                copied = CatalogLoader(source, target).run(dry_run=args.dry_run)
            finally:
                source.dispose()
                target.dispose()
        except LoadError as error:
            print(f"Catalog load FAILED: {error}", file=sys.stderr)
            return 1

    print(f"  done in {time.perf_counter() - started:.0f} s")
    for name, count in copied.items():
        print(f"  {name}: {count}")
    print("Dry run - rolled back, nothing written." if args.dry_run else "Catalog loaded.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
