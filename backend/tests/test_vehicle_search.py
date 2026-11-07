"""Covers app/services/vehicle_search.py against the seeded demo catalog:
Mazda CX-5 Prime-Line (petrol FWD, 104 kW, 824 900 Kč) and Centre-Line
(petrol AWD, 104 kW, 1 023 900 Kč); VW Tiguan People (diesel FWD, 110 kW,
1 176 000 Kč) and R-Line People (petrol AWD, 150 kW, 1 459 000 Kč).
"""

import pytest

from app.models.enums import Drivetrain, FuelType
from app.schemas.search import VehicleSearchFilters
from app.services.vehicle_search import search_facets, search_vehicles
from tests.conftest import SeededData


def _trims(seeded: SeededData, filters: VehicleSearchFilters, **kwargs: object) -> list[str]:
    return [car.trim for car in search_vehicles(seeded.session, filters, **kwargs).items]


def test_no_filters_returns_everything_cheapest_first(seeded_session: SeededData) -> None:
    page = search_vehicles(seeded_session.session, VehicleSearchFilters())
    assert page.total == 4
    assert [car.trim for car in page.items] == ["Prime-Line", "Centre-Line", "People", "R-Line People"]


@pytest.mark.parametrize(
    ("filters", "expected"),
    [
        (VehicleSearchFilters(price_min=900_000, price_max=1_200_000), ["Centre-Line", "People"]),
        (VehicleSearchFilters(price_max=900_000), ["Prime-Line"]),
        (VehicleSearchFilters(brand_ids=[2]), ["People", "R-Line People"]),
        (VehicleSearchFilters(body_types=["SUV"]), ["Prime-Line", "Centre-Line", "People", "R-Line People"]),
        (VehicleSearchFilters(body_types=["Kombi"]), []),
        (VehicleSearchFilters(fuel_types=[FuelType.diesel, FuelType.electric]), ["People"]),
        (VehicleSearchFilters(drivetrains=[Drivetrain.awd]), ["Centre-Line", "R-Line People"]),
        (VehicleSearchFilters(power_kw_min=105), ["People", "R-Line People"]),
        (VehicleSearchFilters(power_kw_max=110), ["Prime-Line", "Centre-Line", "People"]),
        (VehicleSearchFilters(keyword="tiguan r-line"), ["R-Line People"]),
        (VehicleSearchFilters(keyword="MAZDA"), ["Prime-Line", "Centre-Line"]),
        (VehicleSearchFilters(keyword="100%"), []),
    ],
)
def test_single_filters(seeded_session: SeededData, filters: VehicleSearchFilters, expected: list[str]) -> None:
    assert _trims(seeded_session, filters) == expected


def test_filters_combine_with_and(seeded_session: SeededData) -> None:
    filters = VehicleSearchFilters(drivetrains=[Drivetrain.awd], fuel_types=[FuelType.petrol], price_max=1_100_000)
    assert _trims(seeded_session, filters) == ["Centre-Line"]


def test_equipment_must_be_standard_unless_optional_allowed(seeded_session: SeededData) -> None:
    # Wireless CarPlay is standard on the CX-5 Centre-Line only.
    assert _trims(seeded_session, VehicleSearchFilters(equipment=["bezdrátový carplay"])) == ["Centre-Line"]
    # Harman/Kardon is an optional extra on both Tiguans.
    assert _trims(seeded_session, VehicleSearchFilters(equipment=["harman"])) == []
    assert _trims(seeded_session, VehicleSearchFilters(equipment=["harman"], equipment_include_optional=True)) == [
        "People",
        "R-Line People",
    ]


def test_matching_ignores_case_of_czech_letters(seeded_session: SeededData) -> None:
    # SQLite's lower() leaves "Č" alone - "Čelní airbagy" must still match.
    assert _trims(seeded_session, VehicleSearchFilters(equipment=["čelní airbagy"])) == ["People", "R-Line People"]
    assert _trims(seeded_session, VehicleSearchFilters(equipment=["ČELNÍ AIRBAGY"])) == ["People", "R-Line People"]


def test_every_equipment_term_must_match(seeded_session: SeededData) -> None:
    assert _trims(seeded_session, VehicleSearchFilters(equipment=["isofix", "bezdrátový carplay"])) == []


@pytest.mark.parametrize(
    ("sort", "expected"),
    [
        ("price_desc", ["R-Line People", "People", "Centre-Line", "Prime-Line"]),
        ("power_desc", ["R-Line People", "People", "Prime-Line", "Centre-Line"]),
        ("alpha", ["Centre-Line", "Prime-Line", "People", "R-Line People"]),
        ("nonsense", ["Prime-Line", "Centre-Line", "People", "R-Line People"]),
    ],
)
def test_sorts(seeded_session: SeededData, sort: str, expected: list[str]) -> None:
    assert _trims(seeded_session, VehicleSearchFilters(), sort=sort) == expected


def test_paging_reports_full_total(seeded_session: SeededData) -> None:
    page = search_vehicles(seeded_session.session, VehicleSearchFilters(), page=2, page_size=3)
    assert page.total == 4
    assert [car.trim for car in page.items] == ["R-Line People"]


def test_facets(seeded_session: SeededData) -> None:
    facets = search_facets(seeded_session.session)
    assert [brand.name for brand in facets.brands] == ["Mazda", "Volkswagen"]
    assert facets.body_types == ["SUV"]
    assert (facets.price_min, facets.price_max) == (824_900, 1_459_000)
    assert (facets.power_kw_min, facets.power_kw_max) == (104, 150)
