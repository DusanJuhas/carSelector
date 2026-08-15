from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, BigIntPK

if TYPE_CHECKING:
    from app.models.car_model import CarModel


class Brand(Base):
    __tablename__ = "brands"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True)
    slug: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)

    models: Mapped[list["CarModel"]] = relationship(back_populates="brand")
