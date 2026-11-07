"""The `/search` page's filter sidebar (see `app/ui/search_page.py`): one
collapsible section per parameter group, each control reporting a whole
new `VehicleSearchFilters` through `on_change` as soon as the user
settles on a value (sliders on release, the keyword after a short pause).

Built once per page render and left alone while the user edits it - the
page rebuilds it only when the filters change from outside (an active
filter chip removed, "Zrušit vše"), so typing never loses focus.
"""

import math
from collections.abc import Awaitable, Callable

from nicegui import ui

from app.models.enums import Drivetrain, FuelType
from app.schemas.common import Money
from app.schemas.search import SearchFacets, VehicleSearchFilters
from app.ui.i18n import t
from app.ui.money import format_money
from app.ui.search_state import body_type_label

OnChange = Callable[[VehicleSearchFilters], Awaitable[None]]

PRICE_STEP = 50_000
POWER_STEP = 10

_CHIP = "rounded-control border px-3 py-1.5 text-[13px] font-semibold min-h-0"
_CHIP_ON = f"{_CHIP} border-accent bg-accent-soft text-accent"
_CHIP_OFF = f"{_CHIP} border-border bg-panel text-text"
_SUBLABEL = "text-[11.5px] font-bold uppercase tracking-wide text-subtext"


def slider_bounds(low: float, high: float, step: int) -> tuple[int, int]:
    """Args:
        low: Smallest value in the catalog.
        high: Largest value in the catalog.
        step: Slider step.

    Returns:
        `(low, high)` widened outward to whole steps, at least one step
        apart (a slider needs a non-empty span).
    """
    start = int(math.floor(low / step) * step)
    end = int(math.ceil(high / step) * step)
    return start, max(end, start + step)


def _price_text(amount: float) -> str:
    return format_money(Money(amount=amount, currency="CZK"))


def _section(title: str, *, opened: bool) -> ui.expansion:
    return (
        ui.expansion(title, value=opened)
        .props("dense header-class='px-5 py-3 text-[14px] font-bold text-text'")
        .classes("w-full border-b border-border")
    )


def _chip_group(
    options: list[tuple[object, str]],
    selected: list,
    on_toggle: Callable[[object, bool], Awaitable[None]],
    marker: str,
) -> None:
    """Toggle chips for a multi-choice parameter; each chip restyles
    itself on click (the sidebar isn't rebuilt per change).

    Args:
        options: `(value, label)` pairs.
        selected: Currently picked values.
        on_toggle: Awaited with the value and whether it's now picked.
        marker: Test marker prefix; each chip gets `<marker>-<value>`.
    """
    picked = {value: value in selected for value, _ in options}
    with ui.row().classes("w-full flex-wrap gap-2"):
        for value, label in options:
            # `color=None`: the default "primary" would tint every chip's text accent.
            button = ui.button(label, color=None).props("flat no-caps dense")
            button.classes(_CHIP_ON if picked[value] else _CHIP_OFF)
            button.mark(f"{marker}-{getattr(value, 'value', value)}")

            async def _click(b: ui.button = button, v: object = value) -> None:
                picked[v] = not picked[v]
                b.classes(replace=_CHIP_ON if picked[v] else _CHIP_OFF)
                await on_toggle(v, picked[v])

            button.on_click(_click)


def search_filters(
    get_filters: Callable[[], VehicleSearchFilters],
    facets: SearchFacets | None,
    on_change: OnChange,
) -> None:
    """Builds the filter sidebar's content.

    Args:
        get_filters: Returns the filters as they are now - read at event
            time, so each control changes only its own fields on top of
            whatever the others have set meanwhile.
        facets: Value ranges and options; `None` (load failed) leaves out
            the controls that need them (sliders, brands, body types).
        on_change: Awaited with the new filters after every change.
    """
    filters = get_filters()

    async def update(**changes: object) -> None:
        await on_change(get_filters().model_copy(update=changes))

    def toggle_in(name: str) -> Callable[[object, bool], Awaitable[None]]:
        async def _toggle(value: object, picked: bool) -> None:
            current = [v for v in getattr(get_filters(), name) if v != value]
            await update(**{name: [*current, value] if picked else current})

        return _toggle

    # Keyword
    with ui.column().classes("w-full gap-0 border-b border-border px-5 py-4"):
        keyword = (
            ui.input(t("search.keyword"), value=filters.keyword)
            .props("dense outlined clearable")
            .classes("w-full")
            .mark("search-keyword")
        )

        async def _keyword_changed() -> None:
            await update(keyword=(keyword.value or "").strip())

        keyword.on("update:model-value", _keyword_changed, throttle=0.5, leading_events=False)

    # Price
    if facets is not None and facets.price_max > 0:
        low, high = slider_bounds(facets.price_min, facets.price_max, PRICE_STEP)
        with _section(t("search.sections.price"), opened=True), ui.column().classes("w-full gap-1 px-5 pb-4"):
            price = ui.range(
                min=low,
                max=high,
                step=PRICE_STEP,
                value={"min": filters.price_min or low, "max": filters.price_max or high},
            ).mark("search-price")
            ui.label().classes("text-[13px] font-semibold text-text").bind_text_from(
                price,
                "value",
                backward=lambda v: f"{_price_text(v['min'])} – {_price_text(v['max'])}",
            )

            async def _price_changed() -> None:
                value = price.value
                await update(
                    price_min=value["min"] if value["min"] > low else None,
                    price_max=value["max"] if value["max"] < high else None,
                )

            price.on("change", _price_changed)

    # Brand
    if facets is not None:
        with _section(t("search.sections.brand"), opened=True), ui.column().classes("w-full gap-1 px-5 pb-4"):
            brands = (
                ui.select(
                    {b.id: b.name for b in facets.brands},
                    multiple=True,
                    value=list(filters.brand_ids),
                    with_input=True,
                    label=t("search.brandPlaceholder"),
                )
                .props("dense outlined use-chips")
                .classes("w-full")
                .mark("search-brands")
            )

            async def _brands_changed() -> None:
                await update(brand_ids=list(brands.value or []))

            brands.on_value_change(_brands_changed)

    # Body type
    if facets is not None and facets.body_types:
        with _section(t("search.sections.body"), opened=True), ui.column().classes("w-full px-5 pb-4"):
            _chip_group(
                [(body, body_type_label(body)) for body in facets.body_types],
                filters.body_types,
                toggle_in("body_types"),
                "search-body",
            )

    # Powertrain
    with _section(t("search.sections.powertrain"), opened=True), ui.column().classes("w-full gap-2 px-5 pb-4"):
        ui.label(t("search.fuelType")).classes(_SUBLABEL)
        _chip_group(
            [(fuel, t(f"vehicleDetail.enums.fuelType.{fuel.value}")) for fuel in FuelType],
            filters.fuel_types,
            toggle_in("fuel_types"),
            "search-fuel",
        )
        ui.label(t("search.drivetrain")).classes(f"{_SUBLABEL} mt-2")
        _chip_group(
            [(drive, t(f"search.drivetrains.{drive.value}")) for drive in Drivetrain],
            filters.drivetrains,
            toggle_in("drivetrains"),
            "search-drive",
        )

    # Performance
    if facets is not None and facets.power_kw_max > 0:
        low_kw, high_kw = slider_bounds(facets.power_kw_min, facets.power_kw_max, POWER_STEP)
        with _section(t("search.sections.performance"), opened=False), ui.column().classes("w-full gap-1 px-5 pb-4"):
            power = ui.range(
                min=low_kw,
                max=high_kw,
                step=POWER_STEP,
                value={"min": filters.power_kw_min or low_kw, "max": filters.power_kw_max or high_kw},
            ).mark("search-power")
            ui.label().classes("text-[13px] font-semibold text-text").bind_text_from(
                power,
                "value",
                backward=lambda v: (
                    f"{v['min']} – {v['max']} kW ({round(v['min'] * 1.36)} – {round(v['max'] * 1.36)} "
                    f"{t('vehicleDetail.units.hp')})"
                ),
            )
            ui.label(t("search.powerHint")).classes("text-[12px] text-subtext")

            async def _power_changed() -> None:
                value = power.value
                await update(
                    power_kw_min=int(value["min"]) if value["min"] > low_kw else None,
                    power_kw_max=int(value["max"]) if value["max"] < high_kw else None,
                )

            power.on("change", _power_changed)

    # Equipment
    with _section(t("search.sections.equipment"), opened=False), ui.column().classes("w-full gap-1 px-5 pb-4"):
        equipment = (
            ui.input_chips(t("search.equipmentLabel"), value=list(filters.equipment), new_value_mode="add-unique")
            .props("dense outlined")
            .classes("w-full")
            .mark("search-equipment")
        )
        ui.label(t("search.equipmentHint")).classes("text-[12px] text-subtext")
        optional = ui.checkbox(t("search.equipmentIncludeOptional"), value=filters.equipment_include_optional).classes(
            "text-[13px]"
        )

        async def _equipment_changed() -> None:
            await update(equipment=[term.strip() for term in equipment.value or [] if term.strip()])

        async def _optional_changed() -> None:
            await update(equipment_include_optional=bool(optional.value))

        equipment.on_value_change(_equipment_changed)
        optional.on_value_change(_optional_changed)

    ui.label(t("search.dataNote")).classes("px-5 py-4 text-[12px] text-subtext")
