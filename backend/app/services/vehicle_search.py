"""Parametric vehicle search behind the `/search` page: every filter in
`VehicleSearchFilters` pushed into one SQL query, so `total` and paging
stay correct against the filtered set (the same reasoning as
`catalog.list_vehicles`, which this generalizes - that one stays as it is
for the REST API's documented `/api/vehicles` contract).
"""

from sqlalchemy import ColumnElement, Select, and_, func, or_, select
from sqlalchemy.orm import Session

from app.models import Brand, CarModel, Configuration, OptionAvailability, OptionItem, Powertrain, Price, Trim
from app.models.enums import AvailabilityStatus
from app.schemas.common import Page
from app.schemas.search import SearchFacets, VehicleSearchFilters
from app.schemas.vehicle import VehicleSummary
from app.services.catalog import _SUMMARY_LOAD_OPTIONS, DEFAULT_MARKET, _build_vehicle_summary, list_brands

SEARCH_SORT_OPTIONS = ("price_asc", "price_desc", "power_desc", "alpha")

_SORT_ORDER_BY = {
    "price_asc": (Price.price_incl_vat.asc(), Configuration.id.asc()),
    "price_desc": (Price.price_incl_vat.desc(), Configuration.id.asc()),
    # Unknown power last, whatever the dialect's default NULL ordering.
    "power_desc": (Powertrain.power_kw.is_(None), Powertrain.power_kw.desc(), Price.price_incl_vat.asc()),
    "alpha": (Brand.name.asc(), CarModel.name.asc(), Trim.name.asc(), Configuration.id.asc()),
}


def _like_pattern(text: str) -> str:
    """Args:
        text: Fragment to look for.

    Returns:
        A `LIKE` pattern matching `text` anywhere, with `LIKE`'s own
        wildcards in it escaped (`\\` is the escape character).
    """
    escaped = text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


def _contains_ci(column: ColumnElement[str], text: str) -> ColumnElement[bool]:
    """Case-insensitive "contains", Czech letters included.

    `lower(column) LIKE lower(text)` alone covers Postgres and ASCII, but
    SQLite's `lower()` leaves non-ASCII letters alone - "Škoda" stays
    "Škoda" and "škoda" would never match. So also try the text with a
    capital first letter and in capitals, which covers how names are
    written (and SQLite's `LIKE` already ignores ASCII case).

    Args:
        column: Text column to search in.
        text: Fragment to look for, as typed.

    Returns:
        A condition true when `column` contains `text`.
    """
    variants = {text.capitalize(), text.upper()} - {text.lower()}
    return or_(
        func.lower(column).like(_like_pattern(text.lower()), escape="\\"),
        *(column.like(_like_pattern(variant), escape="\\") for variant in sorted(variants)),
    )


def _apply_filters(stmt: Select, filters: VehicleSearchFilters) -> Select:
    """Args:
        stmt: A select already joined to configurations, trims, models,
            brands, powertrains and the current price row.
        filters: The filters to apply.

    Returns:
        `stmt` narrowed by every set filter.
    """
    for word in filters.keyword.split():
        stmt = stmt.where(
            or_(_contains_ci(Brand.name, word), _contains_ci(CarModel.name, word), _contains_ci(Trim.name, word))
        )
    if filters.price_min is not None or filters.price_max is not None:
        stmt = stmt.where(Price.currency == filters.currency)
    if filters.price_min is not None:
        stmt = stmt.where(Price.price_incl_vat >= filters.price_min)
    if filters.price_max is not None:
        stmt = stmt.where(Price.price_incl_vat <= filters.price_max)
    if filters.brand_ids:
        stmt = stmt.where(Brand.id.in_(filters.brand_ids))
    if filters.body_types:
        stmt = stmt.where(CarModel.category.in_(filters.body_types))
    if filters.fuel_types:
        stmt = stmt.where(Powertrain.fuel_type.in_(filters.fuel_types))
    if filters.drivetrains:
        stmt = stmt.where(Powertrain.drivetrain.in_(filters.drivetrains))
    if filters.power_kw_min is not None:
        stmt = stmt.where(Powertrain.power_kw >= filters.power_kw_min)
    if filters.power_kw_max is not None:
        stmt = stmt.where(Powertrain.power_kw <= filters.power_kw_max)

    statuses = [AvailabilityStatus.standard]
    if filters.equipment_include_optional:
        statuses.append(AvailabilityStatus.optional)
    for term in filters.equipment:
        if not term.strip():
            continue
        # An uncorrelated IN, not a per-row EXISTS: the only index on
        # option_availability leads with option_item_id, so matching the
        # (few) items by name first and then their configurations is fast,
        # while a correlated EXISTS scanned the whole table per car (~20 s
        # on the real catalog).
        stmt = stmt.where(
            Configuration.id.in_(
                select(OptionAvailability.configuration_id)
                .join(OptionItem, OptionAvailability.option_item_id == OptionItem.id)
                .where(
                    OptionAvailability.availability.in_(statuses),
                    _contains_ci(OptionItem.name, term.strip()),
                )
            )
        )
    return stmt


def search_vehicles(
    db: Session,
    filters: VehicleSearchFilters,
    *,
    market: str = DEFAULT_MARKET,
    sort: str = "price_asc",
    page: int = 1,
    page_size: int = 20,
) -> Page[VehicleSummary]:
    """Searches priced configurations by every parameter in `filters`.

    Args:
        db: Database session to query through.
        filters: What to match - see `VehicleSearchFilters`.
        market: Market to price and filter against.
        sort: One of `SEARCH_SORT_OPTIONS`; anything else falls back to
            `"price_asc"`.
        page: 1-indexed page number.
        page_size: Rows per page.

    Returns:
        The requested page, with `total` set to the full matching count.
    """
    current_price_join = and_(
        Price.configuration_id == Configuration.id,
        Price.market == market,
        Price.valid_to.is_(None),
        # A zero price is an import glitch, never a real offer - it would
        # otherwise top every "cheapest first" search.
        Price.price_incl_vat > 0,
    )
    stmt = (
        select(Configuration, Price)
        .join(Trim, Configuration.trim_id == Trim.id)
        .join(CarModel, Trim.model_id == CarModel.id)
        .join(Brand, CarModel.brand_id == Brand.id)
        .join(Powertrain, Configuration.powertrain_id == Powertrain.id)
        .join(Price, current_price_join)
    )
    stmt = _apply_filters(stmt, filters)

    total = db.scalar(select(func.count()).select_from(stmt.with_only_columns(Configuration.id).subquery()))

    order_by = _SORT_ORDER_BY.get(sort, _SORT_ORDER_BY["price_asc"])
    stmt = stmt.options(*_SUMMARY_LOAD_OPTIONS).order_by(*order_by).offset((page - 1) * page_size).limit(page_size)
    rows = db.execute(stmt).unique().all()
    items = [_build_vehicle_summary(configuration, price) for configuration, price in rows]
    return Page(items=items, page=page, page_size=page_size, total=total or 0)


def search_facets(db: Session, *, market: str = DEFAULT_MARKET) -> SearchFacets:
    """Args:
        db: Database session to query through.
        market: Market whose current prices bound the price slider.

    Returns:
        The brands, body types and price/power span the filter controls
        offer. An empty catalog gives zero-width spans.
    """
    body_types = (
        db.execute(
            select(CarModel.category).where(CarModel.category.is_not(None)).distinct().order_by(CarModel.category)
        )
        .scalars()
        .all()
    )
    price_min, price_max = db.execute(
        select(func.min(Price.price_incl_vat), func.max(Price.price_incl_vat)).where(
            Price.market == market, Price.valid_to.is_(None), Price.price_incl_vat > 0
        )
    ).one()
    power_min, power_max = db.execute(select(func.min(Powertrain.power_kw), func.max(Powertrain.power_kw))).one()
    return SearchFacets(
        brands=list_brands(db),
        body_types=list(body_types),
        price_min=float(price_min or 0),
        price_max=float(price_max or 0),
        power_kw_min=int(power_min or 0),
        power_kw_max=int(power_max or 0),
    )
