from dataclasses import dataclass
from datetime import date, datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_db
from app.db.base import Base
from app.main import app
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
    session: Session
    model_id: int
    config_prime_2wd_id: int
    config_centre_awd_id: int


@pytest.fixture()
def db_session():
    # SQLite renders our Postgres-native Enum columns as VARCHAR+CHECK,
    # which is enough to exercise the ORM/API layer end to end without a
    # live Postgres instance (see backend/README.md for why the first
    # migration was verified the same way).
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def seeded_session(db_session: Session) -> SeededData:
    # Explicit ids throughout: SQLAlchemy's BigInteger PK only gets
    # SQLite's autoincrement rowid-aliasing when the column is literally
    # `Integer`, not `BigInteger` - on Postgres this is a non-issue
    # (BIGSERIAL, already verified via the migration DDL), but SQLite
    # raises "NOT NULL constraint failed" on an omitted BigInteger PK.
    brand = Brand(id=1, slug="mazda", name="Mazda")
    db_session.add(brand)
    db_session.flush()

    model = CarModel(id=1, brand_id=brand.id, slug="cx-5", name="CX-5", category="SUV", model_year=2026)
    db_session.add(model)
    db_session.flush()

    prime_line = Trim(id=1, model_id=model.id, name="Prime-Line", display_order=1)
    centre_line = Trim(id=2, model_id=model.id, name="Centre-Line", display_order=2)
    db_session.add_all([prime_line, centre_line])
    db_session.flush()

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
    db_session.add_all([engine_2wd, engine_awd])
    db_session.flush()

    config_prime_2wd = Configuration(id=1, trim_id=prime_line.id, powertrain_id=engine_2wd.id)
    config_centre_awd = Configuration(id=2, trim_id=centre_line.id, powertrain_id=engine_awd.id)
    db_session.add_all([config_prime_2wd, config_centre_awd])
    db_session.flush()

    color = Color(id=1, model_id=model.id, name="Arctic White", finish_type=ColorFinish.solid)
    db_session.add(color)
    db_session.flush()
    db_session.add(
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
    db_session.add(option)
    db_session.flush()
    db_session.add(
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
    db_session.add(source_doc)
    db_session.flush()

    db_session.add_all(
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
    db_session.commit()

    return SeededData(
        session=db_session,
        model_id=model.id,
        config_prime_2wd_id=config_prime_2wd.id,
        config_centre_awd_id=config_centre_awd.id,
    )


@pytest.fixture()
def client(seeded_session: SeededData) -> TestClient:
    def _override_get_db():
        yield seeded_session.session

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
