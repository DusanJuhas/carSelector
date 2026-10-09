"""UI-side calls into `app/services/feedback.py` - each one a
`run.io_bound` around a short-lived session (see `app/ui/db.py`), like
`app/ui/articles_state.py`'s, returning the same `Outcome`.

Refusals come back as the service's error code (a key under
`feedback.errors`), anything unexpected is logged and reported as
`"unknown_error"`.
"""

import logging
from collections.abc import Callable
from typing import TypeVar

from nicegui import run
from sqlalchemy.orm import Session

from app.schemas.feedback import FeedbackContext, FeedbackRead
from app.services import feedback
from app.services.feedback import FeedbackError
from app.ui import db as ui_db
from app.ui.articles_state import Outcome
from app.ui.i18n import current_language

logger = logging.getLogger(__name__)

T = TypeVar("T")


async def _call(action: Callable[[Session], T]) -> Outcome[T]:
    def _run() -> T:
        with ui_db.get_session() as db:
            return action(db)

    try:
        return Outcome(value=await run.io_bound(_run))
    except FeedbackError as exc:
        return Outcome(error=exc.code)
    except Exception:
        logger.exception("Feedback action failed")
        return Outcome(error="unknown_error")


async def submit(user_id: int, feedback_type: str, text: str, context: FeedbackContext) -> Outcome[FeedbackRead]:
    language = current_language()
    return await _call(lambda db: feedback.submit(db, user_id, feedback_type, text, context, language))


async def list_for_admin(admin_id: int, feedback_type: str | None, status: str | None) -> Outcome[list[FeedbackRead]]:
    return await _call(lambda db: feedback.list_for_admin(db, admin_id, feedback_type, status))


async def count_new(admin_id: int) -> Outcome[int]:
    return await _call(lambda db: feedback.count_new(db, admin_id))


async def update(admin_id: int, feedback_id: int, status: str, admin_note: str) -> Outcome[FeedbackRead]:
    return await _call(lambda db: feedback.update(db, admin_id, feedback_id, status, admin_note))
