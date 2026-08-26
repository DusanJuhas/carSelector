"""Port of frontend/src/utils/sortCars.test.ts."""

from app.schemas.common import Money
from app.schemas.vehicle import VehicleSummary
from app.ui.sort import sort_cars


def _car(configuration_id: int, brand: str, model: str, trim: str, amount: float) -> VehicleSummary:
    return VehicleSummary(
        configuration_id=configuration_id,
        brand=brand,
        model=model,
        trim=trim,
        price=Money(amount=amount, currency="CZK"),
        specs=[],
    )


CARS = [
    _car(1, "Toyota", "Corolla", "Comfort", 600_000),
    _car(2, "Mazda", "CX-5", "Prime-Line", 800_000),
    _car(3, "Škoda", "Superb", "Selection", 700_000),
]


def test_recommended_is_a_passthrough() -> None:
    assert sort_cars(CARS, "recommended") == CARS


def test_price_asc() -> None:
    result = sort_cars(CARS, "price_asc")
    assert [c.configuration_id for c in result] == [1, 3, 2]


def test_price_desc() -> None:
    result = sort_cars(CARS, "price_desc")
    assert [c.configuration_id for c in result] == [2, 3, 1]


def test_alpha_orders_by_brand_model_trim() -> None:
    result = sort_cars(CARS, "alpha")
    assert [c.configuration_id for c in result] == [2, 3, 1]  # Mazda, Škoda, Toyota


def test_custom_order_applies_given_ids_first() -> None:
    result = sort_cars(CARS, "custom", custom_order=[3, 1])
    assert [c.configuration_id for c in result] == [3, 1, 2]


def test_custom_order_falls_back_to_input_order_for_unlisted_cars() -> None:
    # Car 2 isn't in custom_order - stays after the ones that are, in its
    # original relative position among the leftovers (stable sort).
    result = sort_cars(CARS, "custom", custom_order=[3])
    assert [c.configuration_id for c in result] == [3, 1, 2]


def test_custom_order_with_no_order_yet_is_a_passthrough() -> None:
    assert sort_cars(CARS, "custom", custom_order=[]) == CARS


def test_does_not_mutate_input() -> None:
    original = list(CARS)
    sort_cars(CARS, "price_asc")
    assert CARS == original
