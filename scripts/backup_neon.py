#!/usr/bin/env python3
"""Backs up the production Postgres database (Neon) to a local folder with
pg_dump, checks the dump, and prunes old ones.

Neon's Free plan can only restore the last 6 hours (capped at 1 GB of
changes) and has no scheduled backups, so this is the copy that covers
anything older - a bad migration noticed later, a deleted project, account
trouble, or moving to another provider. The catalog can always be rebuilt
from storage/scraper.db (scripts/import_scraper_data.py); users, articles,
feedback and shared links can only come back from a dump like this one.

Configuration comes from the environment, so nothing secret ever lands in
the repo or in a scheduled task's command line:

    NEON_BACKUP_URL   Neon's *direct* (not "-pooler") connection string.
                      Neon warns against pg_dump over a pooled connection.
                      A postgresql+psycopg:// URL (the app's form) is
                      accepted too - pg_dump only understands postgresql://.
    NEON_BACKUP_DIR   Where dumps go (or pass --out). Keep it outside the
                      repo: dumps contain users' email addresses.
    PG_BIN            Optional folder holding pg_dump/pg_restore, if they
                      aren't on PATH (e.g. C:\\Program Files\\PostgreSQL\\17\\bin).

The client tools must match the server's major version (Postgres 17 on
Neon - check with `pg_dump -V`).

Usage:

    python scripts/backup_neon.py
    scripts\\backup_neon.bat                       (Windows wrapper, for Task Scheduler)
    python scripts/backup_neon.py --out D:\\backups --keep-daily 30

Each run writes drivewise-YYYYMMDD-HHMMSS.dump (pg_dump custom format:
schema, data and alembic_version), verifies it with `pg_restore --list`,
then deletes dumps that are neither among the newest --keep-daily nor the
first of one of the newest --keep-monthly months. Exits non-zero on any
failure, so a scheduled task shows it as failed.

Restore (into an empty database, e.g. a new Neon project):

    pg_restore -v --no-owner --no-privileges -d "<direct URL>" drivewise-....dump

then point DATABASE_URL at it; the next deploy's `alembic upgrade head`
brings an older dump's schema up to date. See doc/arch/deployment.md.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

DUMP_PREFIX = "drivewise-"
DUMP_SUFFIX = ".dump"
_DUMP_NAME = re.compile(r"^drivewise-(\d{8})-(\d{6})\.dump$")


def libpq_url(url: str) -> str:
    """Turns the app's SQLAlchemy-style URL into one libpq tools accept.

    Args:
        url: A Postgres URL, possibly with a `+driver` part in its scheme.

    Returns:
        The same URL with a plain `postgresql://` scheme.
    """
    scheme, sep, rest = url.partition("://")
    if not sep:
        return url
    if scheme.split("+", 1)[0] in ("postgres", "postgresql"):
        return "postgresql://" + rest
    return url


def dump_timestamp(name: str) -> datetime | None:
    """Reads the timestamp out of a dump's file name.

    Args:
        name: A file name, e.g. `drivewise-20261016-200000.dump`.

    Returns:
        The timestamp, or None for any file this script didn't write - so
        pruning never touches anything else in the folder.
    """
    match = _DUMP_NAME.match(name)
    if not match:
        return None
    return datetime.strptime(match.group(1) + match.group(2), "%Y%m%d%H%M%S")


def dumps_to_delete(names: Iterable[str], keep_daily: int, keep_monthly: int) -> list[str]:
    """Picks the dumps the retention policy no longer needs.

    Kept: the newest `keep_daily` dumps, plus the oldest dump of each of the
    newest `keep_monthly` calendar months (a month's first dump is its most
    complete "start of month" state). Files that aren't this script's dumps
    are ignored entirely.

    Args:
        names: File names in the backup folder.
        keep_daily: How many of the newest dumps to keep regardless of date.
        keep_monthly: How many months keep their first dump.

    Returns:
        File names to delete, oldest first.
    """
    dated = sorted(((ts, name) for name in names if (ts := dump_timestamp(name)) is not None), reverse=True)
    keep = {name for _, name in dated[:keep_daily]}
    first_of_month: dict[tuple[int, int], str] = {}
    for ts, name in dated:  # newest first, so the last write per month is its oldest dump
        first_of_month[(ts.year, ts.month)] = name
    for month in sorted(first_of_month, reverse=True)[:keep_monthly]:
        keep.add(first_of_month[month])
    return [name for _, name in reversed(dated) if name not in keep]


class BackupError(Exception):
    """A backup step failed; the message says which and why."""


@dataclass
class NeonBackup:
    """One backup run: dump, verify, prune.

    Attributes:
        url: libpq connection string (never printed - it holds the password).
        out_dir: Folder for the dumps; created if missing.
        pg_bin: Folder with pg_dump/pg_restore, or None to use PATH.
        keep_daily: See `dumps_to_delete`.
        keep_monthly: See `dumps_to_delete`.
        run: Runs a command; injectable so tests don't need Postgres tools.
        now: Clock; injectable for tests.
    """

    url: str
    out_dir: Path
    pg_bin: Path | None = None
    keep_daily: int = 14
    keep_monthly: int = 12
    run: Callable[[list[str]], subprocess.CompletedProcess] = field(
        default=lambda cmd: subprocess.run(cmd, capture_output=True, text=True)
    )
    now: Callable[[], datetime] = datetime.now

    def tool(self, name: str) -> str:
        """Finds a Postgres client tool.

        Args:
            name: `pg_dump` or `pg_restore`.

        Returns:
            The executable's path.

        Raises:
            BackupError: The tool isn't in `pg_bin` or on PATH.
        """
        found = shutil.which(name, path=str(self.pg_bin)) if self.pg_bin else shutil.which(name)
        if not found:
            where = self.pg_bin or "PATH"
            raise BackupError(
                f"{name} not found in {where} - install the PostgreSQL 17 command-line tools or set PG_BIN"
            )
        return found

    def dump(self) -> Path:
        """Writes a new dump. It goes to a `.partial` file first and is only
        renamed once `verify` passes, so a half-written file never looks
        like a backup (and is never counted by the retention policy).

        Returns:
            The finished dump file.

        Raises:
            BackupError: pg_dump or the verification failed.
        """
        self.out_dir.mkdir(parents=True, exist_ok=True)
        final = self.out_dir / f"{DUMP_PREFIX}{self.now():%Y%m%d-%H%M%S}{DUMP_SUFFIX}"
        partial = final.with_name(final.name + ".partial")
        result = self.run([self.tool("pg_dump"), "-Fc", "--no-password", "-d", self.url, "-f", str(partial)])
        if result.returncode != 0:
            partial.unlink(missing_ok=True)
            raise BackupError(f"pg_dump failed (exit {result.returncode}): {result.stderr.strip()}")
        self.verify(partial)
        partial.replace(final)
        return final

    def verify(self, path: Path) -> None:
        """Checks that a dump is complete enough for pg_restore to read its
        table of contents - a truncated or empty file fails here.

        Args:
            path: The dump to check.

        Raises:
            BackupError: The file is missing, empty, or unreadable.
        """
        if not path.exists() or path.stat().st_size == 0:
            raise BackupError(f"{path.name} is missing or empty")
        result = self.run([self.tool("pg_restore"), "--list", str(path)])
        if result.returncode != 0:
            raise BackupError(f"pg_restore --list can't read {path.name}: {result.stderr.strip()}")

    def prune(self) -> list[str]:
        """Deletes the dumps the retention policy no longer needs.

        Returns:
            Names of the deleted files.
        """
        names = [path.name for path in self.out_dir.iterdir() if path.is_file()]
        doomed = dumps_to_delete(names, self.keep_daily, self.keep_monthly)
        for name in doomed:
            (self.out_dir / name).unlink()
        return doomed


def main(argv: list[str] | None = None) -> int:
    """Runs one backup from the command line.

    Args:
        argv: Arguments (default: `sys.argv[1:]`).

    Returns:
        Process exit code: 0 on success, 1 on a failed backup, 2 on missing
        configuration.
    """
    parser = argparse.ArgumentParser(description="Back up the Neon database with pg_dump.")
    parser.add_argument(
        "--out", type=Path, default=os.getenv("NEON_BACKUP_DIR"), help="backup folder (default: NEON_BACKUP_DIR)"
    )
    parser.add_argument("--keep-daily", type=int, default=14, help="newest dumps to keep (default 14)")
    parser.add_argument("--keep-monthly", type=int, default=12, help="months that keep their first dump (default 12)")
    args = parser.parse_args(argv)

    url = os.getenv("NEON_BACKUP_URL")
    if not url:
        print("NEON_BACKUP_URL is not set (Neon's direct connection string).", file=sys.stderr)
        return 2
    if not args.out:
        print("No backup folder: set NEON_BACKUP_DIR or pass --out.", file=sys.stderr)
        return 2

    pg_bin = os.getenv("PG_BIN")
    job = NeonBackup(
        url=libpq_url(url),
        out_dir=Path(args.out),
        pg_bin=Path(pg_bin) if pg_bin else None,
        keep_daily=args.keep_daily,
        keep_monthly=args.keep_monthly,
    )
    try:
        path = job.dump()
    except BackupError as error:
        print(f"Backup FAILED: {error}", file=sys.stderr)
        return 1
    print(f"Backup OK: {path} ({path.stat().st_size / 1024:.0f} KB)")
    for name in job.prune():
        print(f"Deleted old backup: {name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
