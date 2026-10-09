from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, BigIntPK


class Feedback(Base):
    """Something a logged-in user told us - a bug report, an idea, praise
    or anything else (see `app/services/feedback.py`). Kept after it is
    resolved, like `AuthorRequest`, so the admin console keeps its history.
    """

    __tablename__ = "feedback"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    # `"bug"` | `"idea"` | `"praise"` | `"other"` - plain strings rather
    # than DB enums (same as `author_requests.status`), so adding a value
    # never needs a dialect-specific migration.
    type: Mapped[str] = mapped_column(String(16), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    # What the user was looking at, captured with their knowledge (the
    # dialog lists it) - opaque JSON validated by `app/schemas/feedback.py`'s
    # `FeedbackContext`, same tradeoff as `SharedSnapshot.content_json`.
    context_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    # The UI language the feedback was written from ("cs" | "en").
    language: Mapped[str] = mapped_column(String(8), nullable=False)
    # `"new"` | `"in_progress"` | `"resolved"` | `"wont_fix"` | `"duplicate"`.
    status: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    # Internal note for admins - never shown to the user.
    admin_note: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    # Last status/note change by an admin, and who made it.
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
