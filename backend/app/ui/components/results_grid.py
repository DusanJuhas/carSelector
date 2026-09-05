"""Port of frontend/src/components/ResultsGrid.tsx + CarCard.tsx + SortControl.tsx."""

from collections.abc import Callable

from nicegui import ui

from app.schemas.vehicle import VehicleSummary
from app.ui.i18n import t
from app.ui.money import format_money
from app.ui.sort import SORT_OPTIONS


def sort_control(value: str, on_change: Callable[[str], None]) -> None:
    """Builds the "Seřadit podle" sort dropdown.

    Args:
        value: Currently selected sort option (one of `SORT_OPTIONS`).
        on_change: Called with the newly selected option's value.
    """
    options = {option: t(f"results.sort.{option}") for option in SORT_OPTIONS}
    with ui.row().classes("items-center gap-2 text-[13px] text-subtext"):
        ui.label(t("results.sortBy"))
        ui.select(options, value=value, on_change=lambda e: on_change(e.value)).classes(
            "rounded-control border border-border bg-panel-2 px-2.5 py-1.5 text-[13px] font-semibold text-text"
        ).props("borderless dense options-dense")


def _car_card(car: VehicleSummary, on_select: Callable[[VehicleSummary], None] | None) -> None:
    """Renders one result card - make/model/trim, price, match score,
    spec tags, and an optional flag/AI-explanation line.

    Args:
        car: Vehicle to render.
        on_select: Called with `car` when clicked/Enter-activated; the
            card is only interactive (clickable, focusable) when given.
    """
    is_high_score = car.match_score is not None and car.match_score >= 90
    border_class = "border-accent" if car.top_pick else "border-border"
    with ui.column().classes(
        "relative overflow-hidden rounded-card border bg-panel shadow-card animate-fade-in gap-0 "
        f"{border_class} {'cursor-pointer' if on_select else ''}"
    ) as card:
        if on_select is not None:
            card.props("tabindex=0")
            card.on("click", lambda: on_select(car))
            card.on("keydown.enter", lambda: on_select(car))

        if car.top_pick:
            ui.label(t("car.topMatch")).classes(
                "absolute left-2.5 top-2.5 z-10 rounded-full bg-accent px-2.5 py-1 text-[10.5px] font-bold "
                "uppercase tracking-wide text-accent-text"
            )

        with ui.element("div").classes(
            "flex h-[140px] w-full items-center justify-center px-3 text-center font-mono text-[11px] text-subtext"
        ).style(
            "background-image: repeating-linear-gradient(45deg, var(--color-panel-2), var(--color-panel-2) 10px, "
            "var(--color-border) 10px, var(--color-border) 20px)"
        ):
            ui.label(t("car.photoPlaceholder", make=car.brand, model=car.model))

        with ui.column().classes("w-full gap-2.5 p-4 pt-3.5"):
            with ui.row().classes("w-full items-start justify-between gap-2"):
                with ui.column().classes("gap-0"):
                    ui.label(f"{car.brand} {car.model} {car.trim}").classes("text-[14.5px] font-bold text-text")
                    ui.label(format_money(car.price)).classes("text-[12.5px] text-subtext")
                if car.match_score is not None:
                    score_class = "bg-accent-soft text-accent" if is_high_score else "text-subtext"
                    ui.label(f"{car.match_score}%").classes(
                        f"shrink-0 rounded-full px-2.5 py-1 text-[15px] font-bold {score_class}"
                    )

            with ui.row().classes("w-full flex-wrap gap-1.5"):
                for spec in car.specs:
                    ui.label(spec).classes(
                        "rounded-full border border-border bg-panel-2 px-2.5 py-1 text-[11px] font-semibold text-subtext"
                    )

            if car.flag:
                ui.label(car.flag).classes("w-full rounded-control bg-flag-bg px-2.5 py-1.5 text-[11.5px] text-flag")

            if car.explanation:
                ui.label(car.explanation).classes("w-full text-[12px] italic leading-relaxed text-subtext")


def _card_slot(car: VehicleSummary, on_select: Callable[[VehicleSummary], None], reorderable: bool) -> None:
    """Renders one card in its grid slot (the `relative w-[230px]` wrapper
    plus the optional drag handle) - the loop body shared by `results_grid`
    and `append_car_cards`.

    Args:
        car: Vehicle to render.
        on_select: Called when the card is clicked/activated.
        reorderable: Shows the "⠿" drag handle when true.
    """
    with ui.column().classes("relative w-[230px] gap-0"):
        if reorderable:
            ui.label("⠿").classes(
                "absolute right-2 top-2 z-10 flex h-6 w-6 items-center justify-center rounded-full "
                "bg-panel-2/90 text-[13px] text-subtext"
            ).tooltip(t("results.dragHint"))
        _car_card(car, on_select)


def results_grid(
    cars: list[VehicleSummary],
    on_select: Callable[[VehicleSummary], None],
    reorderable: bool,
    on_reorder: Callable[[list[int]], None] | None,
) -> ui.row | None:
    """Renders the responsive card grid, or an empty-state message.

    Cards are laid out as a wrapping flex row (fixed 230px card width)
    rather than the original CSS grid - visually equivalent for this
    fixed-size-card case, and avoids the sortable container needing a
    `display: grid` that plays awkwardly with `make_sortable`'s DOM
    reordering during drag.

    Args:
        cars: Cars to display, already sorted (see `app/ui/sort.py`).
        on_select: Called when a card is clicked/activated.
        reorderable: Enables drag-to-reorder ("Moje pořadí" sort mode).
        on_reorder: Called with every card's configuration id in its new
            order once a drag completes. Required when `reorderable` is
            `True`.

    Returns:
        The card row container, so a caller doing infinite-scroll paging
        (see `append_car_cards`) can append later pages into it without
        re-rendering the cards already on screen - or `None` if `cars`
        was empty and only the empty-state label was rendered.
    """
    if not cars:
        ui.label(t("results.emptyState")).classes("w-full px-5 py-10 text-center text-[13px] text-subtext")
        return None

    with ui.row().classes("w-full gap-4") as container:
        for car in cars:
            _card_slot(car, on_select, reorderable)

    if reorderable and on_reorder is not None:
        order = [car.configuration_id for car in cars]

        def _on_end(event: object) -> None:
            # SortableEventArguments (nicegui.elements.mixins.sortable_element)
            # carries the drag's old/new position within this container.
            new_order = list(order)
            moved = new_order.pop(event.old_index)  # type: ignore[attr-defined]
            new_order.insert(event.new_index, moved)  # type: ignore[attr-defined]
            on_reorder(new_order)

        container.make_sortable(handle=None, animation=0.15, on_end=_on_end)

    return container


def append_car_cards(container: ui.row, cars: list[VehicleSummary], on_select: Callable[[VehicleSummary], None]) -> None:
    """Appends more cards into an already-rendered `results_grid` container,
    for infinite-scroll paging - without this, loading the next page would
    mean calling `results_grid` again with the *whole* accumulated list,
    which re-sends every already-visible card over the websocket on every
    scroll tick. For a large catalog (hundreds of rows) that repeated
    full-rebuild eventually produces a single update message past
    NiceGUI's ~1MB websocket message limit, disconnecting the client (see
    doc/CHANGELOG.md's infinite-scroll message-size fix entry).

    Only used for non-reorderable grids (`app/ui/pages.py` falls back to a
    full `results_grid` re-render for the "Moje pořadí" custom-sort mode
    instead of calling this) - a reorderable grid's `make_sortable` drag
    handling is set up once in `results_grid` and appending outside that
    isn't worth the added risk for a rarely-combined edge case (dragging
    to reorder while still infinite-scrolling the full browsing catalog).

    Args:
        container: The `ui.row` a prior `results_grid` call returned.
        cars: Only the newly-loaded page's cars, in display order - not
            the full accumulated list.
        on_select: Same callback passed to the original `results_grid` call.
    """
    with container:
        for car in cars:
            _card_slot(car, on_select, reorderable=False)
