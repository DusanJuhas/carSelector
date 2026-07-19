"""Read queries backing the catalog endpoints (brands / models / vehicles).

Deliberately plain SQLAlchemy queries, not a generic repository abstraction -
there are only 5 read shapes and they don't share enough to be worth
hiding behind an interface yet.
"""

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session, joinedload

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
    Trim,
)
from app.models.enums import AvailabilityStatus, Drivetrain, FuelType
from app.schemas.catalog import BrandRead, ModelOverview, TrimOverview
from app.schemas.common import Money, Page
from app.schemas.vehicle import (
    ColorOption,
    OptionLine,
    PowertrainSpec,
    PricePoint,
    VehicleDetail,
    VehicleSummary,
)

DEFAULT_MARKET = "CZ"

_SUMMARY_LOAD_OPTIONS = (
    joinedload(Configuration.trim).joinedload(Trim.model).joinedload(CarModel.brand),
    joinedload(Configuration.powertrain),
)


def _build_powertrain_spec(powertrain: Powertrain) -> PowertrainSpec:
    return PowertrainSpec(
        fuel_type=powertrain.fuel_type,
        transmission=powertrain.transmission,
        drivetrain=powertrain.drivetrain,
        power_kw=powertrain.power_kw,
        power_hp=powertrain.power_hp,
        consumption_min=powertrain.consumption_min,
        consumption_max=powertrain.consumption_max,
        consumption_unit=powertrain.consumption_unit,
        co2_min_g_km=powertrain.co2_min_g_km,
        co2_max_g_km=powertrain.co2_max_g_km,
    )


def _build_specs_tags(powertrain: Powertrain) -> list[str]:
    # Simplified placeholder: the source price lists never state seat
    # count (see doc/api-contract.md "open items"), so this can't yet
    # match the richer ["AWD", "5 seats", "Hybrid"]-style tags from the
    # original design concept - only powertrain-derived tags for now.
    tags = [powertrain.drivetrain.value.upper()]
    if powertrain.fuel_type != FuelType.petrol:
        tags.append(powertrain.fuel_type.value.replace("_", " ").title())
    return tags


def _build_vehicle_summary(configuration: Configuration, price: Price) -> VehicleSummary:
    trim = configuration.trim
    model = trim.model
    return VehicleSummary(
        configuration_id=configuration.id,
        brand=model.brand.name,
        model=model.name,
        trim=trim.name,
        price=Money(amount=float(price.price_incl_vat), currency=price.currency),
        specs=_build_specs_tags(configuration.powertrain),
    )


def list_vehicles(
    db: Session,
    *,
    body_type: str | None = None,
    fuel_type: FuelType | None = None,
    drivetrain: Drivetrain | None = None,
    budget_max: float | None = None,
    currency: str = "CZK",
    market: str = DEFAULT_MARKET,
    page: int = 1,
    page_size: int = 20,
) -> Page[VehicleSummary]:
    """Catalog browse/search, independent of the chat flow.

    `min_seats` from the API contract is intentionally not a parameter
    here yet: the source data has no seat-count field anywhere in the
    schema, so accepting the param and silently ignoring it would be
    worse than not accepting it at all.
    """
    current_price_join = and_(
        Price.configuration_id == Configuration.id,
        Price.market == market,
        Price.valid_to.is_(None),
    )

    stmt = (
        select(Configuration, Price)
        .join(Trim, Configuration.trim_id == Trim.id)
        .join(CarModel, Trim.model_id == CarModel.id)
        .join(Powertrain, Configuration.powertrain_id == Powertrain.id)
        .join(Price, current_price_join)
        .options(*_SUMMARY_LOAD_OPTIONS)
    )
    if body_type:
        stmt = stmt.where(CarModel.category == body_type)
    if fuel_type:
        stmt = stmt.where(Powertrain.fuel_type == fuel_type)
    if drivetrain:
        stmt = stmt.where(Powertrain.drivetrain == drivetrain)
    if budget_max is not None:
        stmt = stmt.where(Price.currency == currency, Price.price_incl_vat <= budget_max)

    total = db.scalar(select(func.count()).select_from(stmt.with_only_columns(Configuration.id).subquery()))

    stmt = stmt.order_by(Configuration.id).offset((page - 1) * page_size).limit(page_size)
    rows = db.execute(stmt).unique().all()

    items = [_build_vehicle_summary(configuration, price) for configuration, price in rows]
    return Page(items=items, page=page, page_size=page_size, total=total or 0)


def get_vehicle_detail(
    db: Session, configuration_id: int, *, market: str = DEFAULT_MARKET
) -> VehicleDetail | None:
    configuration = (
        db.execute(
            select(Configuration)
            .where(Configuration.id == configuration_id)
            .options(*_SUMMARY_LOAD_OPTIONS)
        )
        .unique()
        .scalar_one_or_none()
    )
    if configuration is None:
        return None

    price = db.execute(
        select(Price).where(
            Price.configuration_id == configuration_id,
            Price.market == market,
            Price.valid_to.is_(None),
        )
    ).scalar_one_or_none()
    if price is None:
        return None

    summary = _build_vehicle_summary(configuration, price)

    color_rows = db.execute(
        select(ConfigurationColor, Color)
        .join(Color, ConfigurationColor.color_id == Color.id)
        .where(ConfigurationColor.configuration_id == configuration_id)
    ).all()
    colors = [
        ColorOption(
            name=color.name,
            finish_type=color.finish_type,
            surcharge=Money(amount=float(cc.surcharge_amount), currency=cc.currency),
        )
        for cc, color in color_rows
    ]

    option_rows = db.execute(
        select(OptionAvailability, OptionItem)
        .join(OptionItem, OptionAvailability.option_item_id == OptionItem.id)
        .where(OptionAvailability.configuration_id == configuration_id)
    ).all()
    standard_equipment = [
        item.name for availability, item in option_rows if availability.availability == AvailabilityStatus.standard
    ]
    optional_equipment = [
        OptionLine(
            name=item.name,
            category=item.category,
            surcharge=Money(amount=float(availability.surcharge_amount), currency=availability.currency),
        )
        for availability, item in option_rows
        if availability.availability == AvailabilityStatus.optional
    ]

    price_history_rows = (
        db.execute(
            select(Price)
            .where(Price.configuration_id == configuration_id, Price.market == market)
            .order_by(Price.valid_from)
        )
        .scalars()
        .all()
    )
    price_history = [
        PricePoint(
            valid_from=p.valid_from,
            valid_to=p.valid_to,
            price=Money(amount=float(p.price_incl_vat), currency=p.currency),
            lowest_price_30d=(
                Money(amount=float(p.lowest_price_30d), currency=p.currency)
                if p.lowest_price_30d is not None
                else None
            ),
        )
        for p in price_history_rows
    ]

    return VehicleDetail(
        **summary.model_dump(),
        powertrain=_build_powertrain_spec(configuration.powertrain),
        colors=colors,
        standard_equipment=standard_equipment,
        optional_equipment=optional_equipment,
        price_history=price_history,
    )


def compare_vehicles(
    db: Session, configuration_ids: list[int], *, market: str = DEFAULT_MARKET
) -> tuple[list[VehicleDetail], list[int]]:
    """Returns (found, missing_ids) - the router decides how to report missing ids."""
    found: list[VehicleDetail] = []
    missing: list[int] = []
    for configuration_id in configuration_ids:
        detail = get_vehicle_detail(db, configuration_id, market=market)
        if detail is None:
            missing.append(configuration_id)
        else:
            found.append(detail)
    return found, missing


def list_brands(db: Session) -> list[BrandRead]:
    brands = db.execute(select(Brand).order_by(Brand.name)).scalars().all()
    return [BrandRead(id=b.id, name=b.name, slug=b.slug) for b in brands]


def get_model_overview(db: Session, model_id: int, *, market: str = DEFAULT_MARKET) -> ModelOverview | None:
    model = (
        db.execute(select(CarModel).where(CarModel.id == model_id).options(joinedload(CarModel.brand)))
        .unique()
        .scalar_one_or_none()
    )
    if model is None:
        return None

    trims = (
        db.execute(select(Trim).where(Trim.model_id == model_id).order_by(Trim.display_order, Trim.name))
        .scalars()
        .all()
    )

    current_price_join = and_(
        Price.configuration_id == Configuration.id,
        Price.market == market,
        Price.valid_to.is_(None),
    )

    trim_overviews = []
    for trim in trims:
        rows = (
            db.execute(
                select(Configuration, Price)
                .join(Price, current_price_join)
                .where(Configuration.trim_id == trim.id)
                .options(*_SUMMARY_LOAD_OPTIONS)
            )
            .unique()
            .all()
        )
        configurations = [_build_vehicle_summary(configuration, price) for configuration, price in rows]
        trim_overviews.append(TrimOverview(id=trim.id, name=trim.name, configurations=configurations))

    return ModelOverview(
        brand=model.brand.name,
        model=model.name,
        category=model.category,
        trims=trim_overviews,
    )
