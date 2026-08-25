"""Per-action database sessions for the UI layer.

`@ui.page` functions only get FastAPI's `Depends(get_db)` resolved once,
at the initial page load (NiceGUI registers `@ui.page` as a real FastAPI
route, but every later user action - sending a message, loading another
page, opening the detail modal - happens over the already-open websocket,
not a new HTTP request, so `Depends` never fires again for them). This
module's `get_session` is the same short-lived-session pattern as
`app/api/deps.py`'s `get_db`, just usable from inside an event handler
instead of a route signature.
"""

from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy.orm import Session

from app.db.session import SessionLocal


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """Opens one `Session` for the duration of a single user action.

    Intended to be called from inside `nicegui.run.io_bound` (the service
    calls it wraps are synchronous SQLAlchemy, and would otherwise block
    NiceGUI's asyncio event loop) - see `app/ui/state.py` for the call
    sites.

    Yields:
        A `Session`, closed automatically when the `with` block exits.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
