from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, BigIntPK


class AuthorRequest(Base):
    """A user asking an admin for the author role (see
    `app/services/authors.py`). Kept after it is decided, so the admin
    console can show who granted what and a rejected user can ask again
    with a new row rather than overwriting the old answer.
    """

    __tablename__ = "author_requests"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    # The byline the user wants to publish under - copied to
    # `users.display_name` on approval.
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    # Free text for the admin: who they are, what they want to write about.
    message: Mapped[str] = mapped_column(Text, nullable=False, default="")
    # `"pending"` | `"approved"` | `"rejected"` - plain string rather than a
    # DB enum, so adding a state never needs a dialect-specific migration.
    status: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    decided_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
