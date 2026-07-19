from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, CHAR, ForeignKey, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.color import Color
    from app.models.configuration import Configuration


class ConfigurationColor(Base):
    """Availability + surcharge of one color for one sellable configuration."""

    __tablename__ = "configuration_colors"
    __table_args__ = (UniqueConstraint("configuration_id", "color_id"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    configuration_id: Mapped[int] = mapped_column(ForeignKey("configurations.id"), nullable=False)
    color_id: Mapped[int] = mapped_column(ForeignKey("colors.id"), nullable=False)
    # 0, not null, for included/no-surcharge colors - a color is always
    # available once linked here, just sometimes free.
    surcharge_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(CHAR(3), nullable=False)

    configuration: Mapped["Configuration"] = relationship(back_populates="configuration_colors")
    color: Mapped["Color"] = relationship(back_populates="configuration_colors")
