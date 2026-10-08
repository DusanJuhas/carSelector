"""Covers the car comparison: the row logic (`app/ui/compare.py`), the pick
(`CompareState`), the PDF export, and the flows in the page - picking
cards into the tray, opening the comparison, removing a car, and filling
the pick with a model's trims from the detail dialog.
"""

from pathlib import Path

import pytest
from nicegui.testing import User

from app.models.enums import Drivetrain, FuelType
from app.schemas.common import Money
from app.schemas.vehicle import OptionLine, PowertrainSpec, VehicleDetail
from app.services import catalog
from app.ui.compare import (
    MAX_COMPARE,
    MISSING,
    OPTIONAL,
    STANDARD,
    build_sections,
    default_trim_selection,
    equipment_rows,
    visible_rows,
)
from app.ui.state import CompareState
from app.ui.vehicle_pdf import build_comparison_pdf, comparison_pdf_filename
from tests.conftest import SeededData


def _car(
    configuration_id: int,
    *,
    brand: str = "Škoda",
    trim: str = "Style",
    price: float = 800_000,
    power_kw: int | None = 110,
    standard: list[str] | None = None,
    optional: list[tuple[str, float]] | None = None,
) -> VehicleDetail:
    return VehicleDetail(
        configuration_id=configuration_id,
        model_id=1,
        brand=brand,
        model="Octavia",
        trim=trim,
        price=Money(amount=price, currency="CZK"),
        specs=[],
        powertrain=PowertrainSpec(
            fuel_type=FuelType.petrol,
            transmission="DSG7",
            drivetrain=Drivetrain.fwd,
            power_kw=power_kw,
            power_hp=None,
            consumption_min=None,
            consumption_max=None,
            consumption_unit=None,
            co2_min_g_km=None,
            co2_max_g_km=None,
        ),
        colors=[],
        standard_equipment=standard or [],
        optional_equipment=[
            OptionLine(name=name, category="equipment", surcharge=Money(amount=amount, currency="CZK"))
            for name, amount in (optional or [])
        ],
        price_history=[],
    )


def test_equipment_rows_say_standard_option_or_missing_per_car() -> None:
    cheap = _car(1, standard=["Bluetooth"], optional=[("Vyhřívaný volant", 6_900)])
    rich = _car(2, standard=["Bluetooth", "vyhřívaný  VOLANT"])

    rows = {row.label: row for row in equipment_rows([cheap, rich])}

    assert [cell.kind for cell in rows["Bluetooth"].cells] == [STANDARD, STANDARD]
    assert not rows["Bluetooth"].differs
    # Matched despite case and spacing, labelled with the first spelling.
    wheel = rows["vyhřívaný  VOLANT"]
    assert [cell.kind for cell in wheel.cells] == [OPTIONAL, STANDARD]
    assert wheel.cells[0].text.startswith("+ 6")
    assert wheel.best == {1}  # included beats paying extra
    only_one = equipment_rows([cheap, _car(3)])
    assert [cell.kind for cell in only_one[0].cells] == [STANDARD, MISSING]


def test_sections_mark_the_best_value_and_hide_equal_rows() -> None:
    cars = [_car(1, price=900_000, power_kw=110), _car(2, price=800_000, power_kw=150)]

    overview, powertrain, equipment, colors = build_sections(cars)

    assert overview.rows[0].best == {1}  # cheaper
    power = next(row for row in powertrain.rows if row.best)
    assert power.best == {1}  # stronger
    fuel = powertrain.rows[0]
    assert not fuel.differs and fuel not in visible_rows(powertrain, differences_only=True)
    assert fuel in visible_rows(powertrain, differences_only=False)


def test_mixed_brands_get_no_row_by_row_equipment() -> None:
    sections = build_sections([_car(1, brand="Škoda"), _car(2, brand="Kia")])
    assert len(sections) == 3  # overview, powertrain, colors


def test_match_score_row_only_with_scores() -> None:
    cars = [_car(1), _car(2)]
    assert len(build_sections(cars)[0].rows) == 1
    assert build_sections(cars, {1: 80, 2: 91})[0].rows[1].best == {1}


def test_default_trim_selection_takes_the_nearest_in_price() -> None:
    prices = [500, 600, 700, 800, 900, 1_000]
    assert default_trim_selection(prices, current_index=0) == {0, 1, 2, 3}
    assert default_trim_selection(prices, current_index=4) == {2, 3, 4, 5}


def test_compare_state_keeps_at_most_four_in_pick_order() -> None:
    state = CompareState()
    for configuration_id in range(1, MAX_COMPARE + 1):
        assert state.add(configuration_id, f"car {configuration_id}")
    assert state.is_full
    assert not state.add(99, "one too many")
    assert state.toggle(2, "car 2") is False
    assert state.ids == [1, 3, 4]
    state.replace([(7, "a"), (8, "b"), (9, "c"), (10, "d"), (11, "e")])
    assert state.ids == [7, 8, 9, 10]
    state.clear()
    assert state.items == []


def test_comparison_pdf_renders(seeded_session: SeededData) -> None:
    details, _ = catalog.compare_vehicles(
        seeded_session.session, [seeded_session.config_people_fwd_id, seeded_session.config_rline_awd_id]
    )
    content = build_comparison_pdf(details, differences_only=True)
    assert content.startswith(b"%PDF")
    name = comparison_pdf_filename(details)
    assert name.isascii() and name.endswith(".pdf")


@pytest.mark.usefixtures("patch_ui_session")
@pytest.mark.nicegui_main_file(str(Path(__file__).with_name("_user_main.py")))
async def test_pick_cards_compare_and_remove(user: User, seeded_session: SeededData) -> None:
    people, rline = seeded_session.config_people_fwd_id, seeded_session.config_rline_awd_id
    await user.open("/")
    await user.should_see("v katalogu", retries=100)

    user.find(marker=f"compare-{people}").click()
    await user.should_see(marker="compare-tray")
    user.find(marker="compare-open").click()
    await user.should_see("Vyberte aspoň 2 vozy.")  # one isn't a comparison

    user.find(marker=f"compare-{rline}").click()
    await user.should_see("Porovnat (2)")
    user.find(marker="compare-open").click()
    await user.should_see(marker=f"compare-column-{rline}", retries=100)
    await user.should_see(marker=f"compare-column-{people}")

    user.find(marker=f"compare-remove-{rline}").click()
    await user.should_see("K porovnání zbyl jen jeden vůz", retries=50)

    # The pick is remembered for the browser.
    await user.open("/")
    await user.should_see("Porovnat (1)", retries=100)


@pytest.mark.usefixtures("patch_ui_session")
@pytest.mark.nicegui_main_file(str(Path(__file__).with_name("_user_main.py")))
async def test_compare_trims_from_the_detail(user: User, seeded_session: SeededData) -> None:
    people, rline = seeded_session.config_people_fwd_id, seeded_session.config_rline_awd_id
    await user.open("/")
    await user.should_see("v katalogu", retries=100)

    user.find(marker=f"car-{people}").click()
    await user.should_see(marker="detail-compare-trims", retries=100)
    user.find(marker="detail-compare-trims").click()
    await user.should_see("Které výbavy porovnat?", retries=100)
    await user.should_see("Vybráno 2 z 4", retries=100)

    user.find(marker="trim-picker-confirm").click()
    await user.should_see(marker=f"compare-column-{rline}", retries=100)
    await user.should_see(marker=f"compare-column-{people}")
    await user.should_see("Porovnat (2)")
