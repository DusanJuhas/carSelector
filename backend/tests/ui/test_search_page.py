"""Covers the `/search` page (`app/ui/search_page.py`), its filter sidebar
(`app/ui/components/search_filters.py`) and the active-filter chips
(`app/ui/search_state.py`), against the seeded demo catalog - see
`tests/test_vehicle_search.py` for which car matches what.
"""

from datetime import UTC, datetime
from pathlib import Path

import pytest
from nicegui.testing import User
from sqlalchemy.orm import Session

from app.models import SavedSearch
from app.models import User as UserRow
from app.models.enums import Drivetrain, FuelType
from app.schemas.catalog import BrandRead
from app.schemas.search import SearchFacets, SearchSettings, VehicleSearchFilters
from app.services import saved_searches
from app.ui.components.search_filters import slider_bounds
from app.ui.search_state import SearchState, active_filter_chips
from tests.conftest import SeededData

_FACETS = SearchFacets(
    brands=[BrandRead(id=1, name="Mazda", slug="mazda")],
    body_types=["Kombi"],
    price_min=0,
    price_max=1,
    power_kw_min=0,
    power_kw_max=1,
)


def test_chips_list_each_set_value_and_remove_only_it() -> None:
    filters = VehicleSearchFilters(
        price_max=900_000,
        brand_ids=[1],
        body_types=["Kombi"],
        fuel_types=[FuelType.electric, FuelType.phev],
        drivetrains=[Drivetrain.awd],
        power_kw_min=100,
        equipment=["isofix"],
    )

    chips = active_filter_chips(filters, _FACETS)

    assert [chip.label for chip in chips] == [
        "do 900\xa0000\xa0Kč",
        "Mazda",
        "Kombi",
        "Elektromobil",
        "Plug-in hybrid",
        "4×4",
        "od 100 kW",
        "Výbava: isofix",
    ]
    electric = chips[3].without
    assert electric.fuel_types == [FuelType.phev]
    assert electric.brand_ids == [1]  # everything else stays
    assert chips[0].without.price_max is None


def test_no_chips_without_filters() -> None:
    assert active_filter_chips(VehicleSearchFilters(keyword="  "), None) == []


_SETTINGS = SearchSettings(
    filters=VehicleSearchFilters(fuel_types=[FuelType.electric], price_max=900_000, equipment=["isofix"]),
    sort="power_desc",
)


def _user_id(session: Session, email: str = "driver@example.cz") -> int:
    row = UserRow(email=email, is_admin=False, is_active=True, created_at=datetime.now(UTC))
    session.add(row)
    session.commit()
    return row.id


async def test_anonymous_settings_round_trip_through_the_browser() -> None:
    storage: dict = {}
    first = SearchState(storage=storage)
    first.filters, first.sort = _SETTINGS.filters, _SETTINGS.sort
    await first.remember()

    second = SearchState(storage=storage)
    await second.restore()

    assert second.filters == _SETTINGS.filters
    assert second.sort == "power_desc"


async def test_logged_in_settings_live_in_the_account(patch_ui_session: Session) -> None:
    user_id = _user_id(patch_ui_session)
    browser: dict = {}
    first = SearchState(storage=browser, user_id=user_id)
    first.filters, first.sort = _SETTINGS.filters, _SETTINGS.sort
    await first.remember()

    assert browser == {}  # nothing left behind in a possibly shared browser
    assert saved_searches.load(patch_ui_session, user_id) == _SETTINGS

    other_device = SearchState(storage={}, user_id=user_id)
    await other_device.restore()
    assert other_device.filters == _SETTINGS.filters
    assert other_device.sort == "power_desc"


async def test_first_login_adopts_the_browser_settings(patch_ui_session: Session) -> None:
    user_id = _user_id(patch_ui_session)
    browser = {SearchState.STORAGE_KEY: _SETTINGS.model_dump(mode="json")}

    state = SearchState(storage=browser, user_id=user_id)
    await state.restore()

    assert state.filters == _SETTINGS.filters
    assert saved_searches.load(patch_ui_session, user_id) == _SETTINGS


async def test_account_settings_win_over_the_browser(patch_ui_session: Session) -> None:
    user_id = _user_id(patch_ui_session)
    saved_searches.save(patch_ui_session, user_id, SearchSettings(filters=VehicleSearchFilters(brand_ids=[2])))
    browser = {SearchState.STORAGE_KEY: _SETTINGS.model_dump(mode="json")}

    state = SearchState(storage=browser, user_id=user_id)
    await state.restore()

    assert state.filters.brand_ids == [2]
    assert state.filters.fuel_types == []


def test_saved_search_service_ignores_an_outdated_shape(patch_ui_session: Session) -> None:
    user_id = _user_id(patch_ui_session)
    assert saved_searches.load(patch_ui_session, user_id) is None
    saved_searches.save(patch_ui_session, user_id, _SETTINGS)
    saved_searches.save(patch_ui_session, user_id, SearchSettings(sort="alpha"))  # overwrites
    assert saved_searches.load(patch_ui_session, user_id) == SearchSettings(sort="alpha")

    row = patch_ui_session.query(SavedSearch).filter_by(user_id=user_id).one()
    row.settings_json = '{"filters": {"fuel_types": ["steam"]}}'
    patch_ui_session.commit()
    assert saved_searches.load(patch_ui_session, user_id) is None


@pytest.mark.parametrize(
    "saved",
    [
        None,
        "garbage",
        {"filters": {"fuel_types": ["steam"]}, "sort": "power_desc"},  # unknown fuel: whole entry ignored
        {"filters": {"price_max": "lots"}},
    ],
)
async def test_unreadable_saved_settings_are_ignored(saved: object) -> None:
    state = SearchState(storage={SearchState.STORAGE_KEY: saved})
    await state.restore()
    assert state.filters == VehicleSearchFilters()
    assert state.sort == "price_asc"


async def test_unknown_saved_sort_keeps_default() -> None:
    state = SearchState(storage={SearchState.STORAGE_KEY: {"filters": {"brand_ids": [2]}, "sort": "bogus"}})
    await state.restore()
    assert state.filters.brand_ids == [2]
    assert state.sort == "price_asc"


@pytest.mark.parametrize(
    ("low", "high", "step", "expected"),
    [(824_900, 1_459_000, 50_000, (800_000, 1_500_000)), (0, 0, 10, (0, 10)), (104, 150, 10, (100, 150))],
)
def test_slider_bounds(low: float, high: float, step: int, expected: tuple[int, int]) -> None:
    assert slider_bounds(low, high, step) == expected


@pytest.mark.usefixtures("patch_ui_session")
@pytest.mark.nicegui_main_file(str(Path(__file__).with_name("_user_main.py")))
async def test_search_page_filters_and_chips(user: User, seeded_session: SeededData) -> None:
    await user.open("/search")
    await user.should_see("4 vozy odpovídají", retries=100)

    user.find(marker="search-drive-awd").click()
    await user.should_see("2 vozy odpovídají", retries=100)
    await user.should_see(marker=f"car-{seeded_session.config_rline_awd_id}")
    await user.should_not_see(marker=f"car-{seeded_session.config_people_fwd_id}")

    user.find(marker="search-fuel-diesel").click()
    await user.should_see("Žádný vůz neodpovídá", retries=100)

    # Removing the diesel chip (fuel chips come before drivetrain ones)
    # leaves the AWD filter in place.
    await user.should_see(marker="search-chip-1")
    user.find(marker="search-chip-0").click()
    await user.should_see("2 vozy odpovídají", retries=100)

    user.find(marker="search-clear").click()
    await user.should_see("4 vozy odpovídají", retries=100)


@pytest.mark.usefixtures("patch_ui_session")
@pytest.mark.nicegui_main_file(str(Path(__file__).with_name("_user_main.py")))
async def test_search_page_remembers_filters_across_visits(user: User, seeded_session: SeededData) -> None:
    await user.open("/search")
    await user.should_see("4 vozy odpovídají", retries=100)
    user.find(marker="search-drive-awd").click()
    await user.should_see("2 vozy odpovídají", retries=100)

    await user.open("/search")  # a later visit, same browser
    await user.should_see("2 vozy odpovídají", retries=100)
    await user.should_see(marker="search-chip-0")
    await user.should_not_see(marker=f"car-{seeded_session.config_people_fwd_id}")

    user.find(marker="search-clear").click()
    await user.should_see("4 vozy odpovídají", retries=100)
    await user.open("/search")
    await user.should_see("4 vozy odpovídají", retries=100)


@pytest.mark.usefixtures("patch_ui_session")
@pytest.mark.nicegui_main_file(str(Path(__file__).with_name("_user_main.py")))
async def test_main_page_links_to_search(user: User) -> None:
    await user.open("/")
    await user.should_see(marker="nav-search", retries=100)
    user.find(marker="menu-search").click()  # the phones' way in
    await user.should_see("Najděte auto podle parametrů", retries=100)
    await user.open("/search")
    await user.should_see("Najděte auto podle parametrů")
    await user.should_see(marker="nav-assistant")


@pytest.mark.usefixtures("patch_ui_session")
@pytest.mark.nicegui_main_file(str(Path(__file__).with_name("_user_main.py")))
async def test_logged_in_filters_come_back_at_the_next_login(
    user: User, seeded_session: SeededData, log_in: object
) -> None:
    await user.open("/")
    await log_in(user, "driver@example.cz")  # type: ignore[operator]
    await user.open("/search")
    await user.should_see("4 vozy odpovídají", retries=100)
    user.find(marker="search-drive-awd").click()
    await user.should_see("2 vozy odpovídají", retries=100)

    await user.open("/")
    user.find(marker="logout").click()
    await user.should_see("Přihlásit se", retries=100)
    # Logged out, the same browser shows none of the account's filters.
    await user.open("/search")
    await user.should_see("4 vozy odpovídají", retries=100)

    await user.open("/")
    await log_in(user, "driver@example.cz")  # type: ignore[operator]
    await user.open("/search")
    await user.should_see("2 vozy odpovídají", retries=100)
    await user.should_see(marker="search-chip-0")
