"""Catalog-browsing filter controls: manufacturer, engine type (fuel type)
and drivetrain. Sits next to `sort_control` (see `app/ui/components/
results_grid.py`) and, like the backend sort options, is only meaningful
in browsing mode - once the AI has narrowed the catalog via chat, the
requirements drawer is the filter mechanism instead (see `app/ui/pages.py`).
"""

from collections.abc import Callable

from nicegui import ui

from app.models.enums import Drivetrain, FuelType
from app.schemas.catalog import BrandRead
from app.ui.i18n import t


def _select(label: str, options: dict[object, str], value: object, on_change: Callable[[object], None]) -> None:
    """One labeled filter dropdown, styled like `sort_control`'s select.

    Args:
        label: Text shown before the dropdown.
        options: Mapping of option value (including `None` for "all") to
            display label.
        value: Currently selected option value.
        on_change: Called with the newly selected option's value.
    """
    with ui.row().classes("items-center gap-2 text-[13px] text-subtext"):
        ui.label(label)
        ui.select(options, value=value, on_change=lambda e: on_change(e.value)).classes(
            "rounded-control border border-border bg-panel-2 px-2.5 py-1.5 text-[13px] font-semibold text-text"
        ).props("borderless dense options-dense")


def filter_bar(
    brands: list[BrandRead],
    brand_id: int | None,
    fuel_type: FuelType | None,
    drivetrain: Drivetrain | None,
    on_brand_change: Callable[[int | None], None],
    on_fuel_type_change: Callable[[FuelType | None], None],
    on_drivetrain_change: Callable[[Drivetrain | None], None],
) -> None:
    """Builds the manufacturer / engine-type / drivetrain filter row.

    Args:
        brands: Every brand in the catalog, for the manufacturer dropdown.
        brand_id: Currently selected brand id, or `None` for "all".
        fuel_type: Currently selected fuel type, or `None` for "all".
        drivetrain: Currently selected drivetrain, or `None` for "all".
        on_brand_change: Called with the newly selected brand id.
        on_fuel_type_change: Called with the newly selected fuel type.
        on_drivetrain_change: Called with the newly selected drivetrain.
    """
    with ui.row().classes("mb-3.5 w-full flex-wrap items-center gap-4"):
        brand_options: dict[object, str] = {None: t("results.filters.all")}
        brand_options.update({brand.id: brand.name for brand in brands})
        _select(t("results.filters.brand"), brand_options, brand_id, on_brand_change)

        fuel_options: dict[object, str] = {None: t("results.filters.all")}
        fuel_options.update({ft: t(f"vehicleDetail.enums.fuelType.{ft.value}") for ft in FuelType})
        _select(t("results.filters.fuelType"), fuel_options, fuel_type, on_fuel_type_change)

        drivetrain_options: dict[object, str] = {None: t("results.filters.all")}
        drivetrain_options.update({dt: t(f"vehicleDetail.enums.drivetrain.{dt.value}") for dt in Drivetrain})
        _select(t("results.filters.drivetrain"), drivetrain_options, drivetrain, on_drivetrain_change)
