"""Per-connection state of the `/search` page (see `app/ui/search_page.py`):
the current filters, the loaded result pages and the filter controls'
value ranges. Like `app/ui/state.py`, every service call goes through
`run.io_bound`.

Also `active_filter_chips`: the removable "active filter" chips above the
results, as pure data so it can be tested without a browser.
"""

import logging
from collections.abc import Callable, MutableMapping
from dataclasses import dataclass, field

from nicegui import run
from pydantic import ValidationError

from app.schemas.common import Money
from app.schemas.search import SearchFacets, SearchSettings, VehicleSearchFilters
from app.schemas.vehicle import VehicleSummary
from app.services import saved_searches, vehicle_search
from app.ui import db as ui_db
from app.ui.i18n import t
from app.ui.money import format_money

logger = logging.getLogger(__name__)

PAGE_SIZE = 20


@dataclass
class FilterChip:
    """One active filter as shown above the results.

    Attributes:
        label: Chip text, e.g. "Elektromobil" or "do 900 000 Kč".
        without: The current filters with just this one removed - what
            clicking the chip's close icon applies.
    """

    label: str
    without: VehicleSearchFilters


def body_type_label(value: str) -> str:
    """Args:
        value: A `models.category` value, e.g. "Kombi".

    Returns:
        Its translated name, or `value` itself for a category the
        translations don't know yet (categories come from imported data).
    """
    try:
        return t(f"search.bodyTypes.{value}")
    except KeyError:
        return value


def active_filter_chips(filters: VehicleSearchFilters, facets: SearchFacets | None) -> list[FilterChip]:
    """Args:
        filters: The current filters.
        facets: The value ranges, for brand names; `None` shows brand ids.

    Returns:
        One chip per set filter value, in sidebar order.
    """
    chips: list[FilterChip] = []

    def add(label: str, **changes: object) -> None:
        chips.append(FilterChip(label=label, without=filters.model_copy(update=changes)))

    def remove_from(name: str, value: object) -> dict[str, list]:
        return {name: [v for v in getattr(filters, name) if v != value]}

    if filters.keyword.strip():
        add(f"„{filters.keyword.strip()}“", keyword="")
    if filters.price_min is not None or filters.price_max is not None:
        add(_range_label(filters.price_min, filters.price_max, _price), price_min=None, price_max=None)
    brand_names = {b.id: b.name for b in facets.brands} if facets else {}
    for brand_id in filters.brand_ids:
        add(brand_names.get(brand_id, str(brand_id)), **remove_from("brand_ids", brand_id))
    for body in filters.body_types:
        add(body_type_label(body), **remove_from("body_types", body))
    for fuel in filters.fuel_types:
        add(t(f"vehicleDetail.enums.fuelType.{fuel.value}"), **remove_from("fuel_types", fuel))
    for drivetrain in filters.drivetrains:
        add(t(f"search.drivetrains.{drivetrain.value}"), **remove_from("drivetrains", drivetrain))
    if filters.power_kw_min is not None or filters.power_kw_max is not None:
        add(_range_label(filters.power_kw_min, filters.power_kw_max, _kw), power_kw_min=None, power_kw_max=None)
    for term in filters.equipment:
        add(f"{t('search.chips.equipment')}: {term}", **remove_from("equipment", term))
    return chips


def _price(amount: float) -> str:
    return format_money(Money(amount=amount, currency="CZK"))


def _kw(value: float) -> str:
    return f"{int(value)} kW"


def _range_label(low: float | None, high: float | None, fmt: Callable[[float], str]) -> str:
    if low is not None and high is not None:
        return f"{fmt(low)} – {fmt(high)}"
    if low is not None:
        return t("search.chips.from", value=fmt(low))
    return t("search.chips.upTo", value=fmt(high))  # type: ignore[arg-type]


@dataclass
class SearchState:
    """Filters plus the results fetched for them so far (page by page)."""

    filters: VehicleSearchFilters = field(default_factory=VehicleSearchFilters)
    sort: str = "price_asc"
    facets: SearchFacets | None = None
    cars: list[VehicleSummary] = field(default_factory=list)
    page: int = 0
    total: int = 0
    is_loading: bool = False
    is_loading_more: bool = False
    error: bool = False
    # Bumped by every `search()`; a response for an older one is dropped,
    # so quick successive filter changes can't land out of order.
    _generation: int = 0
    # Where an anonymous visitor's filters and sort are kept between
    # visits - `app.storage.user` in the app (per browser, like
    # `CompareState`'s pick), `None` to keep nothing.
    storage: MutableMapping | None = None
    # The logged-in user, whose settings are kept in their account instead
    # (`app/services/saved_searches.py`) - so they come back at the next
    # login, on any device. `None` while anonymous.
    user_id: int | None = None

    STORAGE_KEY = "search_settings"

    @property
    def has_more(self) -> bool:
        return len(self.cars) < self.total

    def _settings(self) -> SearchSettings:
        return SearchSettings(filters=self.filters, sort=self.sort)

    def _apply(self, settings: SearchSettings) -> None:
        self.filters = settings.filters
        if settings.sort in vehicle_search.SEARCH_SORT_OPTIONS:
            self.sort = settings.sort

    def _browser_settings(self) -> SearchSettings | None:
        """Returns:
        What the browser has stored, or `None` if nothing (readable) -
        e.g. saved by an older version with a different filter shape.
        """
        saved = self.storage.get(self.STORAGE_KEY) if self.storage is not None else None
        if not isinstance(saved, dict):
            return None
        try:
            return SearchSettings.model_validate(saved)
        except ValidationError:
            return None

    async def restore(self) -> None:
        """Loads the settings `remember` last stored, if any.

        A logged-in user gets their account's settings. If the account
        has none yet, whatever they set in this browser before logging in
        is adopted - and saved to the account, so it's there next time.
        Anonymous visitors get this browser's settings. Nothing found (or
        a failing load) leaves the search empty.
        """
        if self.user_id is not None:
            user_id = self.user_id

            def _load() -> SearchSettings | None:
                with ui_db.get_session() as db:
                    return saved_searches.load(db, user_id)

            try:
                account = await run.io_bound(_load)
            except Exception:
                logger.exception("Loading saved search settings failed")
                account = None
            if account is not None:
                self._apply(account)
                return
            browser = self._browser_settings()
            if browser is not None:
                self._apply(browser)
                await self.remember()
            return
        browser = self._browser_settings()
        if browser is not None:
            self._apply(browser)

    async def remember(self) -> None:
        """Stores the current filters and sort for the next visit - in the
        account when logged in, in the browser otherwise. A failing save
        is only logged: the search itself goes on."""
        settings = self._settings()
        if self.user_id is not None:
            user_id = self.user_id

            def _save() -> None:
                with ui_db.get_session() as db:
                    saved_searches.save(db, user_id, settings)

            try:
                await run.io_bound(_save)
            except Exception:
                logger.exception("Saving search settings failed")
            return
        if self.storage is not None:
            # A new dict (not an in-place edit), so a persistent storage
            # notices the change and writes it out.
            self.storage[self.STORAGE_KEY] = settings.model_dump(mode="json")

    async def load_facets(self) -> None:
        """Loads the filter controls' value ranges; leaves `facets` as
        `None` if the query fails (the page then offers no sliders)."""

        def _load() -> SearchFacets:
            with ui_db.get_session() as db:
                return vehicle_search.search_facets(db)

        try:
            self.facets = await run.io_bound(_load)
        except Exception:
            self.facets = None

    def _fetch(self, page: int) -> Callable[[], object]:
        filters, sort = self.filters.model_copy(deep=True), self.sort

        def _load() -> object:
            with ui_db.get_session() as db:
                return vehicle_search.search_vehicles(db, filters, sort=sort, page=page, page_size=PAGE_SIZE)

        return _load

    async def search(self) -> None:
        """(Re)loads page 1 for the current filters and sort."""
        self._generation += 1
        generation = self._generation
        self.is_loading = True
        self.error = False
        try:
            result = await run.io_bound(self._fetch(1))
        except Exception:
            if generation == self._generation:
                self.error = True
                self.cars, self.total, self.page = [], 0, 0
                self.is_loading = False
            return
        if generation != self._generation:
            return
        self.cars, self.total, self.page = result.items, result.total, result.page
        self.is_loading = False

    async def load_more(self) -> list[VehicleSummary]:
        """Appends the next page.

        Returns:
            Just the newly loaded cars - empty if nothing more to load, a
            load is already running, or the filters changed meanwhile.
        """
        if self.is_loading or self.is_loading_more or not self.has_more:
            return []
        self.is_loading_more = True
        generation = self._generation
        try:
            result = await run.io_bound(self._fetch(self.page + 1))
        except Exception:
            return []
        finally:
            self.is_loading_more = False
        if generation != self._generation:
            return []
        self.cars = [*self.cars, *result.items]
        self.page, self.total = result.page, result.total
        return result.items
