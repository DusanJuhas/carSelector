from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, BigIntPK


class SavedSearch(Base):
    """A logged-in user's last `/search` page settings (`SearchSettings`
    in `app/schemas/search.py`: filters + sort), serialized as JSON - so
    they come back at the next login, on any device. One row per user,
    overwritten on every change, like `SavedRequirements` - see
    `app/services/saved_searches.py`.
    """

    __tablename__ = "saved_searches"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, nullable=False)
    # SearchSettings.model_dump_json() - opaque JSON for the same reason
    # as `SavedRequirements.requirements_json`: one source of truth for
    # the shape (the Pydantic schema), only ever loaded/replaced whole.
    settings_json: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
