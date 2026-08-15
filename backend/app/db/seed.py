"""Demo catalog data: one real, hand-verified vehicle (Mazda CX-5) drawn from
the price list in storage/cars/mazda/cx-5/ - see backend/README.md's Tests
section for how the source figures were verified.

`seed_demo_data()` is the single source of truth for this dataset, shared by:
- tests/conftest.py's `seeded_session` fixture (in-memory SQLite, per test)
- `python -m app.db.seed` (this module's __main__ block, against whatever
  DATABASE_URL points at - the persistent SQLite file by default)

IDs are assigned explicitly rather than left to autoincrement, so seeding is
deterministic and the two callers stay in sync without copy-pasting data.
"""
from dataclasses import dataclass
from datetime import date, datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    Brand,
    CarModel,
    Color,
    Configuration,
    ConfigurationColor,
    OptionAvailability,
    OptionItem,
    Powertrain,
    Price,
    SourceDocument,
    Trim,
)
from app.models.enums import (
    AvailabilityStatus,
    ColorFinish,
    Drivetrain,
    DocumentType,
    FuelType,
    OptionCategory,
)


@dataclass
class SeededData:
    model_id: int
    config_prime_2wd_id: int
    config_centre_awd_id: int


def seed_demo_data(session: Session) -> SeededData:
    brand = Brand(id=1, slug="mazda", name="Mazda")
    session.add(brand)
    session.flush()

    model = CarModel(id=1, brand_id=brand.id, slug="cx-5", name="CX-5", category="SUV", model_year=2026)
    session.add(model)
    session.flush()

    prime_line = Trim(id=1, model_id=model.id, name="Prime-Line", display_order=1)
    centre_line = Trim(id=2, model_id=model.id, name="Centre-Line", display_order=2)
    session.add_all([prime_line, centre_line])
    session.flush()

    engine_2wd = Powertrain(
        id=1,
        model_id=model.id,
        fuel_type=FuelType.petrol,
        transmission="6-speed automatic",
        drivetrain=Drivetrain.fwd,
        power_kw=104,
        power_hp=141,
        consumption_min=7.0,
        consumption_max=7.0,
        consumption_unit="l_100km",
        co2_min_g_km=157,
        co2_max_g_km=159,
    )
    engine_awd = Powertrain(
        id=2,
        model_id=model.id,
        fuel_type=FuelType.petrol,
        transmission="6-speed automatic",
        drivetrain=Drivetrain.awd,
        power_kw=104,
        power_hp=141,
        consumption_min=7.4,
        consumption_max=7.5,
        consumption_unit="l_100km",
        co2_min_g_km=168,
        co2_max_g_km=169,
    )
    session.add_all([engine_2wd, engine_awd])
    session.flush()

    config_prime_2wd = Configuration(id=1, trim_id=prime_line.id, powertrain_id=engine_2wd.id)
    config_centre_awd = Configuration(id=2, trim_id=centre_line.id, powertrain_id=engine_awd.id)
    session.add_all([config_prime_2wd, config_centre_awd])
    session.flush()

    color = Color(id=1, model_id=model.id, name="Arctic White", finish_type=ColorFinish.solid)
    session.add(color)
    session.flush()
    session.add(
        ConfigurationColor(
            id=1,
            configuration_id=config_prime_2wd.id,
            color_id=color.id,
            surcharge_amount=0,
            currency="CZK",
        )
    )

    option = OptionItem(
        id=1, model_id=model.id, category=OptionCategory.equipment, name="17-inch alloy wheels"
    )
    session.add(option)
    session.flush()
    session.add(
        OptionAvailability(
            id=1,
            option_item_id=option.id,
            configuration_id=config_prime_2wd.id,
            availability=AvailabilityStatus.standard,
        )
    )

    source_doc = SourceDocument(
        id=1,
        model_id=model.id,
        file_path="storage/cars/mazda/cx-5/mazda_cx-5_akcni_cenik_2026-07_cz.pdf",
        document_type=DocumentType.price_list,
        market="CZ",
        locale="cs-CZ",
        effective_date=date(2025, 9, 22),
        campaign_valid_from=date(2026, 7, 1),
        campaign_valid_to=date(2026, 9, 30),
        retrieved_at=datetime.now(timezone.utc),
    )
    session.add(source_doc)
    session.flush()

    session.add_all(
        [
            Price(
                id=1,
                configuration_id=config_prime_2wd.id,
                source_document_id=source_doc.id,
                market="CZ",
                currency="CZK",
                list_price=875_900,
                discount_amount=51_000,
                price_incl_vat=824_900,
                lowest_price_30d=875_900,
                valid_from=date(2026, 7, 1),
                valid_to=None,
                scraped_at=datetime.now(timezone.utc),
            ),
            Price(
                id=2,
                configuration_id=config_centre_awd.id,
                source_document_id=source_doc.id,
                market="CZ",
                currency="CZK",
                list_price=1_074_900,
                discount_amount=51_000,
                price_incl_vat=1_023_900,
                lowest_price_30d=1_074_900,
                valid_from=date(2026, 7, 1),
                valid_to=None,
                scraped_at=datetime.now(timezone.utc),
            ),
        ]
    )
    session.commit()

    return SeededData(
        model_id=model.id,
        config_prime_2wd_id=config_prime_2wd.id,
        config_centre_awd_id=config_centre_awd.id,
    )


def main() -> None:
    """`python -m app.db.seed` - creates tables if missing (equivalent to
    `alembic upgrade head` for this single-migration schema) and seeds the
    demo catalog, unless the DB already has data (safe to re-run).
    """
    from app.db.base import Base
    from app.db.session import SessionLocal, engine

    Base.metadata.create_all(engine)

    session = SessionLocal()
    try:
        if session.scalar(select(Brand.id).limit(1)) is not None:
            print("Database already has catalog data - skipping seed. "
                  "Delete drivewise.db (or point DATABASE_URL elsewhere) to reseed.")
            return
        data = seed_demo_data(session)
        print(
            f"Seeded 1 brand / 1 model / {2} configurations "
            f"(model_id={data.model_id}, configuration_ids="
            f"{data.config_prime_2wd_id},{data.config_centre_awd_id}) into "
            f"{engine.url}"
        )
    finally:
        session.close()


if __name__ == "__main__":
    main()
