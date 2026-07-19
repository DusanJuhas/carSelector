from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey, SmallInteger, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.brand import Brand
    from app.models.color import Color
    from app.models.option_item import OptionItem
    from app.models.powertrain import Powertrain
    from app.models.source_document import SourceDocument
    from app.models.trim import Trim


class CarModel(Base):
    """A vehicle nameplate, e.g. "Mazda CX-5". Maps to table `models`.

    Named CarModel (not Model) to avoid colliding with the generic "Model"
    term used by SQLAlchemy/Django-style ORM conventions elsewhere.
    """

    __tablename__ = "models"
    __table_args__ = (UniqueConstraint("brand_id", "slug"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    brand_id: Mapped[int] = mapped_column(ForeignKey("brands.id"), nullable=False)
    slug: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    # Body type (e.g. "SUV"). Nullable: never a structured field in the
    # source price lists, only inferable from marketing prose.
    category: Mapped[str | None] = mapped_column(String(64))
    # Soft/informational only - neither sample source document gives a
    # clean, reliable model-year field tied to price rows.
    model_year: Mapped[int | None] = mapped_column(SmallInteger)
    description: Mapped[str | None] = mapped_column(Text)

    brand: Mapped["Brand"] = relationship(back_populates="models")
    trims: Mapped[list["Trim"]] = relationship(back_populates="model")
    powertrains: Mapped[list["Powertrain"]] = relationship(back_populates="model")
    colors: Mapped[list["Color"]] = relationship(back_populates="model")
    option_items: Mapped[list["OptionItem"]] = relationship(back_populates="model")
    source_documents: Mapped[list["SourceDocument"]] = relationship(back_populates="model")
