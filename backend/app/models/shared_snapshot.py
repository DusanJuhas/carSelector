from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, BigIntPK


class SharedSnapshot(Base):
    """A frozen, read-only copy of a result someone chose to share - served
    at `/s/<token>` to anyone with the link, no account needed (see
    `app/services/sharing.py`).

    A snapshot, not a live view: prices and the car list stay as they were
    when it was shared, which is the point when it's shown at a dealership
    ("price as of 25. 9."). The content is opaque JSON validated by
    `app/schemas/sharing.py`'s `SharedSnapshotContent`, same tradeoff as
    `SavedRequirements.requirements_json`.
    """

    __tablename__ = "shared_snapshots"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True)
    # Random, URL-safe, unguessable (`secrets.token_urlsafe`) - never a
    # sequential id, so links can't be enumerated.
    token: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    content_json: Mapped[str] = mapped_column(Text, nullable=False)
    # Who shared it, for a future "my shared links" list - never shown to
    # a link's viewers. Null for anonymous shares.
    created_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
