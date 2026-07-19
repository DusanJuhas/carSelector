from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, CHAR, CheckConstraint, ForeignKey, Numeric, UniqueConstraint
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import AvailabilityStatus

if TYPE_CHECKING:
    from app.models.configuration import Configuration
    from app.models.option_item import OptionItem


class OptionAvailability(Base):
    """Whether one option_item is standard/optional/unavailable for one
    specific configuration (trim x powertrain), and its surcharge if
    optional.

    Scoped to the full configuration (not just trim) so that engine- or
    drivetrain-gated rules - e.g. Mazda's "Hill Descent Control: AWD
    only", or VW's engine-code-restricted option codes - are just
    ordinary rows, not a special case. The tradeoff: a trim-level fact
    (the common case) is duplicated across every powertrain variant of
    that trim.
    """

    __tablename__ = "option_availability"
    __table_args__ = (
        UniqueConstraint("option_item_id", "configuration_id"),
        CheckConstraint(
            "(availability = 'optional') = (surcharge_amount IS NOT NULL)",
            name="surcharge_set_iff_optional",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    option_item_id: Mapped[int] = mapped_column(ForeignKey("option_items.id"), nullable=False)
    configuration_id: Mapped[int] = mapped_column(ForeignKey("configurations.id"), nullable=False)
    availability: Mapped[AvailabilityStatus] = mapped_column(
        SAEnum(AvailabilityStatus, name="availability_status"), nullable=False
    )
    # Null when standard or unavailable; set when optional.
    surcharge_amount: Mapped[float | None] = mapped_column(Numeric(12, 2))
    currency: Mapped[str | None] = mapped_column(CHAR(3))

    option_item: Mapped["OptionItem"] = relationship(back_populates="availabilities")
    configuration: Mapped["Configuration"] = relationship(back_populates="option_availabilities")
