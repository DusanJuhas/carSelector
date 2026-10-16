"""Tests for scripts/backup_neon.py - URL handling, the retention policy,
and a backup run against fake pg_dump/pg_restore (no Postgres needed)."""

import importlib.util
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import pytest

_SPEC = importlib.util.spec_from_file_location(
    "backup_neon_script", Path(__file__).resolve().parents[1] / "backup_neon.py"
)
backup_neon = importlib.util.module_from_spec(_SPEC)
# Registered before running it: @dataclass looks its module up there.
sys.modules[_SPEC.name] = backup_neon
_SPEC.loader.exec_module(backup_neon)


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("postgresql+psycopg://u:p@h/db?sslmode=require", "postgresql://u:p@h/db?sslmode=require"),
        ("postgres://u:p@h/db", "postgresql://u:p@h/db"),
        ("postgresql://u:p@h/db", "postgresql://u:p@h/db"),
    ],
)
def test_libpq_url(url: str, expected: str) -> None:
    assert backup_neon.libpq_url(url) == expected


def test_dump_timestamp_ignores_foreign_files() -> None:
    assert backup_neon.dump_timestamp("drivewise-20261016-200000.dump") == datetime(2026, 10, 16, 20, 0, 0)
    assert backup_neon.dump_timestamp("drivewise-20261016-200000.dump.partial") is None
    assert backup_neon.dump_timestamp("notes.txt") is None


def _daily(year: int, month: int, days: range) -> list[str]:
    return [f"drivewise-{year}{month:02d}{day:02d}-200000.dump" for day in days]


def test_retention_keeps_newest_dailies_and_first_of_each_month() -> None:
    names = _daily(2026, 8, range(1, 32)) + _daily(2026, 9, range(1, 31)) + _daily(2026, 10, range(1, 17))
    doomed = backup_neon.dumps_to_delete(names + ["readme.txt"], keep_daily=14, keep_monthly=12)
    kept = set(names) - set(doomed)
    assert kept == set(_daily(2026, 10, range(3, 17))) | {
        "drivewise-20260801-200000.dump",
        "drivewise-20260901-200000.dump",
        "drivewise-20261001-200000.dump",
    }
    assert "readme.txt" not in doomed
    assert doomed == sorted(doomed)  # oldest first


def test_retention_drops_months_beyond_keep_monthly() -> None:
    names = [f"drivewise-2025{month:02d}01-200000.dump" for month in range(1, 13)] + ["drivewise-20260101-200000.dump"]
    doomed = backup_neon.dumps_to_delete(names, keep_daily=1, keep_monthly=12)
    assert doomed == ["drivewise-20250101-200000.dump"]


def _fake_tools(fail: str | None = None):
    """A `run` stand-in: pg_dump writes a file, pg_restore --list reads it."""
    calls: list[list[str]] = []

    def run(cmd: list[str]) -> subprocess.CompletedProcess:
        calls.append(cmd)
        tool = Path(cmd[0]).stem
        if tool == fail:
            return subprocess.CompletedProcess(cmd, 1, "", f"{tool} broke")
        if tool == "pg_dump":
            Path(cmd[cmd.index("-f") + 1]).write_bytes(b"PGDMP fake")
        return subprocess.CompletedProcess(cmd, 0, "", "")

    return run, calls


@pytest.fixture()
def tools_on_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(backup_neon.shutil, "which", lambda name, path=None: f"/fake/bin/{name}")


def test_backup_run_writes_verifies_and_prunes(tmp_path: Path, tools_on_path: None) -> None:
    old = tmp_path / "drivewise-20250101-200000.dump"
    old.write_bytes(b"old")
    run, calls = _fake_tools()
    job = backup_neon.NeonBackup(
        url="postgresql://u:p@h/db",
        out_dir=tmp_path,
        keep_daily=1,
        keep_monthly=1,
        run=run,
        now=lambda: datetime(2026, 10, 16, 20, 0, 0),
    )
    path = job.dump()
    assert path == tmp_path / "drivewise-20261016-200000.dump"
    assert path.read_bytes() == b"PGDMP fake"
    assert [Path(cmd[0]).stem for cmd in calls] == ["pg_dump", "pg_restore"]
    assert "--no-password" in calls[0]  # never waits for a prompt under Task Scheduler
    assert job.prune() == ["drivewise-20250101-200000.dump"]
    assert not old.exists()


@pytest.mark.parametrize("failing_tool", ["pg_dump", "pg_restore"])
def test_failed_backup_leaves_no_dump(tmp_path: Path, tools_on_path: None, failing_tool: str) -> None:
    run, _ = _fake_tools(fail=failing_tool)
    job = backup_neon.NeonBackup(url="postgresql://u:p@h/db", out_dir=tmp_path, run=run)
    with pytest.raises(backup_neon.BackupError, match=failing_tool):
        job.dump()
    assert not any(p.name.endswith(".dump") for p in tmp_path.iterdir())


def test_main_requires_configuration(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("NEON_BACKUP_URL", raising=False)
    assert backup_neon.main(["--out", "x"]) == 2
    monkeypatch.setenv("NEON_BACKUP_URL", "postgresql://u:p@h/db")
    monkeypatch.delenv("NEON_BACKUP_DIR", raising=False)
    assert backup_neon.main([]) == 2


def test_missing_tool_is_reported(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(backup_neon.shutil, "which", lambda name, path=None: None)
    job = backup_neon.NeonBackup(url="postgresql://u:p@h/db", out_dir=tmp_path)
    with pytest.raises(backup_neon.BackupError, match="pg_dump not found"):
        job.dump()
