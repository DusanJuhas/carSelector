from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    CHAR,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.configuration import Configuration
    from app.models.source_document import SourceDocument


class Price(Base):
    """Append-only price history for one configuration.

    Rows are never updated in place: a changed price is a new row with
    `valid_from` = today, after closing the previous row's `valid_to` =
    today. "Current price" is the row with `valid_to IS NULL`, enforced
    by the partial unique index below - at most one open-ended row per
    (configuration, market) at a time. "Price as of date D" is
    `valid_from <= D AND (valid_to IS NULL OR valid_to > D)`.

    `lowest_price_30d` stores the source's own disclosed reference price
    (the EU Omnibus-directive-style disclosure seen in the Mazda sample)
    as reported - it is never derived from our own `valid_from` history,
    since our scrape cadence isn't guaranteed to match the window the
    manufacturer is attesting to.
    """

    __tablename__ = "prices"
    __table_args__ = (
        Index(
            "uq_prices_current_per_configuration_market",
            "configuration_id",
            "market",
            unique=True,
            postgresql_where="valid_to IS NULL",
        ),
        CheckConstraint("valid_to IS NULL OR valid_to > valid_from", name="valid_to_after_valid_from"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    configuration_id: Mapped[int] = mapped_column(ForeignKey("configurations.id"), nullable=False)
    source_document_id: Mapped[int] = mapped_column(ForeignKey("source_documents.id"), nullable=False)
    market: Mapped[str] = mapped_column(String(8), nullable=False)
    currency: Mapped[str] = mapped_column(CHAR(3), nullable=False)
    list_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    discount_amount: Mapped[float | None] = mapped_column(Numeric(12, 2))
    price_incl_vat: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    # VW provides this directly; Mazda's price list doesn't - never
    # derive/fabricate it from an assumed VAT rate.
    price_excl_vat: Mapped[float | None] = mapped_column(Numeric(12, 2))
    # Stored only when the source discloses it, so incl/excl VAT can be
    # cross-derived without hardcoding a VAT rate anywhere in application
    # logic.
    vat_rate: Mapped[float | None] = mapped_column(Numeric(4, 3))
    lowest_price_30d: Mapped[float | None] = mapped_column(Numeric(12, 2))
    valid_from: Mapped[date] = mapped_column(Date, nullable=False)
    valid_to: Mapped[date | None] = mapped_column(Date)
    scraped_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    configuration: Mapped["Configuration"] = relationship(back_populates="prices")
    source_document: Mapped["SourceDocument"] = relationship(back_populates="prices")
