from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, BigIntPK


class LikedModel(Base):
    """One car model (`models` row) a logged-in user has liked from a
    results card - see `app/services/liked_models.py`.

    Deliberately scoped to the *model* (e.g. "Škoda Kodiaq"), not to a
    `configuration`: a like expresses taste in the car itself, not in one
    particular trim × engine, so every card of that model shows as liked
    and gets the ranking boost (see `RecommendationEngine`).
    """

    __tablename__ = "liked_models"
    __table_args__ = (UniqueConstraint("user_id", "model_id"),)

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    model_id: Mapped[int] = mapped_column(ForeignKey("models.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
