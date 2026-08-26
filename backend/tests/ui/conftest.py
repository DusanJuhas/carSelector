"""Fixtures for the UI test suite. Reuses `tests/conftest.py`'s seeded
in-memory database (real service calls against deterministic seed data,
same as the API test suite) by monkeypatching `app.ui.db.get_session` to
yield it - there's no wire format to fake here, unlike the former
frontend's `vi.mock('../api/*')`.
"""

from collections.abc import Generator
from contextlib import contextmanager

import pytest
from sqlalchemy.orm import Session

import app.ui.db as ui_db
from tests.conftest import SeededData, seeded_session  # noqa: F401 - re-exported fixture


@pytest.fixture()
def patch_ui_session(seeded_session: SeededData, monkeypatch: pytest.MonkeyPatch) -> Session:
    """Makes every `app.ui.db.get_session()` call in the UI layer yield
    the same seeded session `seeded_session` provides to the API test
    suite, instead of opening a real connection to `DATABASE_URL`.

    `app/ui/state.py` calls this via `ui_db.get_session()` (a module
    attribute lookup at call time), not a `from app.ui.db import
    get_session` copy - patching the attribute here is what makes that
    lookup pick up the fake.

    Args:
        seeded_session: The seeded in-memory session (see `tests/conftest.py`).
        monkeypatch: Standard pytest fixture, undoes the patch after the test.

    Returns:
        The same `Session` `app.ui.db.get_session()` now yields.
    """

    @contextmanager
    def _fake_get_session() -> Generator[Session, None, None]:
        yield seeded_session.session

    monkeypatch.setattr(ui_db, "get_session", _fake_get_session)
    return seeded_session.session
