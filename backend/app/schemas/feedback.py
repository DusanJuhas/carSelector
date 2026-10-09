"""User feedback as the UI layer sees it (see `app/services/feedback.py`).
Internal to the app, like `app/schemas/article.py`: not part of the REST
contract in doc/api-contract.md.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from app.schemas.requirement import StructuredRequirements

FeedbackType = Literal["bug", "idea", "praise", "other"]
FeedbackStatus = Literal["new", "in_progress", "resolved", "wont_fix", "duplicate"]
FEEDBACK_TYPES: tuple[FeedbackType, ...] = ("bug", "idea", "praise", "other")
FEEDBACK_STATUSES: tuple[FeedbackStatus, ...] = ("new", "in_progress", "resolved", "wont_fix", "duplicate")


class FeedbackContext(BaseModel):
    """What the user was looking at when they wrote - all of it listed in
    the dialog before sending, so nothing is collected silently.
    """

    # Which part of the app the dialog was opened from, e.g. "search".
    page: str = ""
    # The `0.y.z` from `doc/CHANGELOG.md`'s newest entry, if readable.
    app_version: str | None = None
    # Only when the user ticked "attach my current requirements".
    requirements: StructuredRequirements | None = None


class FeedbackRead(BaseModel):
    """One feedback item, for the admin console."""

    id: int
    user_id: int
    email: str
    type: FeedbackType
    text: str
    context: FeedbackContext
    language: str
    status: FeedbackStatus
    admin_note: str
    created_at: datetime
    updated_at: datetime | None
