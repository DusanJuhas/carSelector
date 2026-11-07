"""Parametric ("advanced") vehicle search - the filter set behind the
`/search` page (see `app/ui/search_page.py`) and the value ranges its
controls offer. Consumed by `app/services/vehicle_search.py`.

Only parameters the catalog actually holds data for are here. Weight,
dimensions, seats, boot volume, towing capacity, EV range and Euro NCAP
aren't stored anywhere yet (neither in `powertrains`/`models` nor in the
scraper's database), and torque/acceleration/consumption/CO2 are filled
for well under 1 % of powertrains - a filter on those would silently hide
nearly the whole catalog, so they're left out until the data exists.
"""

from pydantic import BaseModel, Field

from app.models.enums import Drivetrain, FuelType
from app.schemas.catalog import BrandRead


class VehicleSearchFilters(BaseModel):
    """Every filter is optional; an empty list / `None` means "any". Lists
    are OR within one parameter (e.g. any of the picked fuel types) and
    the parameters are AND-ed together. `equipment` is the exception: a
    car must have every listed feature.
    """

    # Whitespace-separated words, each of which must appear in the brand,
    # model or trim name (case-insensitive).
    keyword: str = ""
    price_min: float | None = None
    price_max: float | None = None
    currency: str = "CZK"
    brand_ids: list[int] = Field(default_factory=list)
    # Exact `models.category` values, as `SearchFacets.body_types` lists them.
    body_types: list[str] = Field(default_factory=list)
    fuel_types: list[FuelType] = Field(default_factory=list)
    drivetrains: list[Drivetrain] = Field(default_factory=list)
    # Cars whose power is unknown are excluded once either bound is set.
    power_kw_min: int | None = None
    power_kw_max: int | None = None
    # Substrings of equipment names (case-insensitive), e.g. "tepelné čerpadlo".
    equipment: list[str] = Field(default_factory=list)
    # False: the feature must be standard; True: standard or optional.
    equipment_include_optional: bool = False


class SearchSettings(BaseModel):
    """What the `/search` page remembers between visits: the filters and
    the sort order (one of `vehicle_search.SEARCH_SORT_OPTIONS`) - in the
    browser for anonymous visitors, in the account for logged-in users
    (see `app/services/saved_searches.py`)."""

    filters: VehicleSearchFilters = Field(default_factory=VehicleSearchFilters)
    sort: str = "price_asc"


class SearchFacets(BaseModel):
    """What the filter controls can offer: brands, body types and the
    catalog's price/power span (for the sliders' ends)."""

    brands: list[BrandRead]
    body_types: list[str]
    price_min: float
    price_max: float
    power_kw_min: int
    power_kw_max: int
