from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey, SmallInteger, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.car_model import CarModel
    from app.models.configuration import Configuration


class Trim(Base):
    """A named equipment grade within a model, e.g. "Prime-Line", "People"."""

    __tablename__ = "trims"
    __table_args__ = (UniqueConstraint("model_id", "name"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    model_id: Mapped[int] = mapped_column(ForeignKey("models.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    display_order: Mapped[int | None] = mapped_column(SmallInteger)
    description: Mapped[str | None] = mapped_column(Text)

    model: Mapped["CarModel"] = relationship(back_populates="trims")
    configurations: Mapped[list["Configuration"]] = relationship(back_populates="trim")
