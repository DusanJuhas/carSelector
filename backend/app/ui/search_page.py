"""`/search`: finding a car by explicit parameters instead of the AI chat -
a filter sidebar (`app/ui/components/search_filters.py`) next to the
results, which reuse the main page's cards, detail dialog and comparison.

The comparison pick lives in `app.storage.user` (see `CompareState`), so
cars picked here are still picked on the main page and vice versa.

Phones show either the filters or the results (toggled by the bottom bar),
like the main page's chat/results tabs.

Registered from `app/main.py`, like `app/ui/articles_page.py`'s pages.
"""

import asyncio
import logging

from nicegui import app, ui
from nicegui.events import GenericEventArguments

from app.schemas.search import VehicleSearchFilters
from app.schemas.vehicle import VehicleSummary
from app.services.vehicle_search import SEARCH_SORT_OPTIONS
from app.ui.auth import AuthState
from app.ui.compare import MAX_COMPARE, MIN_COMPARE
from app.ui.components.compare_dialog import compare_dialog, trim_picker_dialog
from app.ui.components.results_grid import CompareToggles, append_car_cards, results_grid
from app.ui.components.search_filters import search_filters
from app.ui.components.share_dialog import share_dialog
from app.ui.components.vehicle_detail_modal import vehicle_detail_modal
from app.ui.i18n import LANGUAGES, current_language, set_language, t, t_count
from app.ui.pages import MOBILE_HIDDEN, MOBILE_VIEWPORT
from app.ui.search_state import SearchState, active_filter_chips
from app.ui.state import CompareState, create_shared_snapshot
from app.ui.styles import register_styles

logger = logging.getLogger(__name__)

# Same lead distance as the main page's infinite scroll (see `pages.py`).
_LOAD_MORE_THRESHOLD_PX = 600

_NAV_LINK = "whitespace-nowrap rounded-control px-3 py-1.5 text-[13px] font-semibold no-underline max-md:px-2"


def _top_bar(on_switch_language: object) -> None:
    """Brand, the AI-assistant / advanced-search / articles links, language.

    Args:
        on_switch_language: Click handler of the language button.
    """
    with ui.row().classes(
        "w-full shrink-0 flex-nowrap items-center justify-between gap-3 border-b border-border bg-panel px-4 py-3 md:px-7"
    ):
        with ui.row().classes("min-w-0 flex-nowrap items-center gap-2 md:gap-4"):
            # Phones: no room - the "AI asistent" pill links home too.
            ui.link(t("header.brand"), "/").classes("text-[17px] font-bold text-text no-underline max-md:hidden!")
            with ui.row().classes("flex-nowrap items-center gap-1 rounded-control bg-panel-2 p-1"):
                ui.link(t("search.navAssistant"), "/").classes(f"{_NAV_LINK} text-subtext").mark("nav-assistant")
                ui.link(t("search.navLink"), "/search").classes(f"{_NAV_LINK} bg-panel text-text shadow-sm")
            ui.link(t("header.articles"), "/articles").classes(f"{_NAV_LINK} text-subtext max-md:hidden!")
        # Icon only on phones - the label doesn't fit next to the nav pills.
        with (
            ui.button(icon="translate", on_click=on_switch_language)
            .props("flat dense no-caps")
            .classes("shrink-0 text-[13px] text-subtext")
            .tooltip(t("header.switchLanguage"))
            .mark("language-toggle")
        ):
            ui.label(t("header.switchLanguage")).classes("ml-1 max-md:hidden!")


def register_search_page() -> None:
    """Registers `@ui.page("/search")` as a side effect - called once from
    `app/main.py`."""

    @ui.page("/search", viewport=MOBILE_VIEWPORT, title=t("search.pageTitle"))
    async def search_page() -> None:
        register_styles()
        # Loading until the first search lands (see the end of this
        # function), so the first paint doesn't claim "0 cars".
        # Logged-in users keep their search settings in their account (see
        # `SearchState.restore`), so the login is read first.
        auth_state = AuthState()
        await auth_state.refresh()
        state = SearchState(
            is_loading=True,
            storage=app.storage.user,
            user_id=auth_state.user.id if auth_state.user else None,
        )
        # The previous visit's filters and sort - restored before anything
        # is built, so the sidebar's controls show them from the start.
        await state.restore()
        compare_state = CompareState(storage=app.storage.user)
        grid_ref: dict[str, ui.row | None] = {"row": None}
        mobile = {"filters_open": False}

        # --- comparison / detail / share (same wiring as pages.py) ---
        open_share = share_dialog()

        async def share(cars: list[VehicleSummary]) -> None:
            try:
                snapshot = await create_shared_snapshot([], cars, None)
            except Exception:
                logger.exception("Creating a shared snapshot failed")
                ui.notify(t("share.error"), type="negative")
                return
            open_share(snapshot)

        async def share_vehicle(detail: VehicleSummary) -> None:
            await share([VehicleSummary.model_validate(detail.model_dump(include=set(VehicleSummary.model_fields)))])

        def on_compare_changed() -> None:
            compare_toggles.sync()
            compare_tray.refresh()

        def toggle_compare(car: VehicleSummary) -> bool:
            was_picked = compare_state.contains(car.configuration_id)
            picked = compare_state.toggle(car.configuration_id, f"{car.brand} {car.model} {car.trim}")
            if not was_picked and not picked:
                ui.notify(t("compare.full", max=MAX_COMPARE))
            on_compare_changed()
            return picked

        compare_toggles = CompareToggles(compare_state.contains, toggle_compare)

        async def open_detail_for(configuration_id: int) -> None:
            await open_detail(configuration_id)

        async def open_comparison_after_picker() -> None:
            on_compare_changed()
            await open_comparison()

        open_trim_picker = trim_picker_dialog(compare_state, open_comparison_after_picker)
        open_detail = vehicle_detail_modal(share_vehicle, compare_state.contains, toggle_compare, open_trim_picker)
        open_comparison = compare_dialog(compare_state, on_compare_changed, open_detail_for, share, lambda: {})

        async def start_comparison() -> None:
            if len(compare_state.ids) < MIN_COMPARE:
                ui.notify(t("compare.needTwo"))
                return
            await open_comparison()

        def clear_comparison() -> None:
            compare_state.clear()
            on_compare_changed()

        # --- searching ---
        def refresh_results() -> None:
            filters_title.refresh()
            results_header.refresh()
            results_body.refresh()
            mobile_bar.refresh()

        async def apply_filters(filters: VehicleSearchFilters) -> None:
            state.filters = filters
            await state.remember()
            await state.search()
            refresh_results()

        async def replace_filters(filters: VehicleSearchFilters) -> None:
            """For changes made outside the sidebar (chips, "clear all") -
            the sidebar's controls are rebuilt to show them."""
            await apply_filters(filters)
            sidebar.refresh()

        async def change_sort(value: str) -> None:
            state.sort = value
            await state.remember()
            await state.search()
            refresh_results()

        def switch_language() -> None:
            language = current_language()
            set_language(LANGUAGES[(LANGUAGES.index(language) + 1) % len(LANGUAGES)])
            ui.navigate.reload()

        def set_mobile_filters(open_: bool) -> None:
            mobile["filters_open"] = open_
            if open_:
                filters_panel.classes(remove=MOBILE_HIDDEN)
                results_panel.classes(add=MOBILE_HIDDEN)
            else:
                filters_panel.classes(add=MOBILE_HIDDEN)
                results_panel.classes(remove=MOBILE_HIDDEN)
            mobile_bar.refresh()

        async def on_results_scroll(event: GenericEventArguments) -> None:
            metrics = event.args or {}
            distance = metrics.get("scrollHeight", 0) - metrics.get("scrollTop", 0) - metrics.get("clientHeight", 0)
            if distance > _LOAD_MORE_THRESHOLD_PX or not state.has_more or state.is_loading_more:
                return
            load = asyncio.ensure_future(state.load_more())
            await asyncio.sleep(0)
            loading_more.refresh()
            new_cars = await load
            loading_more.refresh()
            if new_cars and grid_ref["row"] is not None:
                append_car_cards(
                    grid_ref["row"], new_cars, lambda car: open_detail(car.configuration_id), None, compare_toggles
                )

        with ui.column().classes("h-[100dvh] w-full flex-col overflow-hidden bg-bg text-text gap-0"):
            _top_bar(switch_language)

            with ui.row().classes("relative min-h-0 w-full flex-1 flex-nowrap gap-0 overflow-clip"):
                with (
                    ui.column()
                    .classes(
                        f"h-full w-full md:w-[340px] shrink-0 overflow-y-auto border-r border-border bg-panel gap-0 "
                        f"{MOBILE_HIDDEN}"
                    )
                    .mark("filters-panel") as filters_panel
                ):

                    @ui.refreshable
                    def filters_title() -> None:
                        # Refreshed with the results, unlike the rest of
                        # the sidebar (see `sidebar` below).
                        count = len(active_filter_chips(state.filters, state.facets))
                        ui.label(f"{t('search.filtersTitle')} ({count})").classes("text-[16px] font-bold text-text")

                    @ui.refreshable
                    def sidebar() -> None:
                        with ui.row().classes(
                            "w-full flex-nowrap items-center justify-between border-b border-border px-5 py-3"
                        ):
                            filters_title()
                            ui.button(
                                t("search.clearAll"), on_click=lambda: replace_filters(VehicleSearchFilters())
                            ).props("flat dense no-caps").classes("text-[13px] font-semibold text-accent").mark(
                                "search-clear"
                            )
                        search_filters(lambda: state.filters, state.facets, apply_filters)

                    sidebar()

                with (
                    ui.column()
                    .classes("min-w-0 h-full flex-1 overflow-y-auto px-4 py-4 md:px-7 md:py-6 gap-0")
                    .on(
                        "scroll",
                        on_results_scroll,
                        throttle=0.2,
                        js_handler=(
                            "(event) => emit({scrollTop: event.target.scrollTop, "
                            "scrollHeight: event.target.scrollHeight, clientHeight: event.target.clientHeight})"
                        ),
                    )
                    .mark("results-panel") as results_panel
                ):

                    @ui.refreshable
                    def results_header() -> None:
                        with ui.row().classes("mb-3 w-full flex-wrap items-end justify-between gap-3"):
                            with ui.column().classes("min-w-0 gap-0.5"):
                                ui.label(t("search.title")).classes(
                                    "text-[22px] md:text-[26px] font-bold leading-tight text-text"
                                )
                                if state.is_loading and not state.cars:
                                    count_text = t("search.loading")
                                else:
                                    count_text = t_count("search.resultsTitle", state.total)
                                ui.label(count_text).classes("text-[14px] font-semibold text-accent").mark(
                                    "search-count"
                                )
                            with ui.row().classes("flex-nowrap items-center gap-2 text-[13px] text-subtext"):
                                ui.label(t("results.sortBy"))
                                ui.select(
                                    {option: t(f"search.sort.{option}") for option in SEARCH_SORT_OPTIONS},
                                    value=state.sort,
                                    on_change=lambda e: change_sort(e.value),
                                ).props("borderless dense options-dense").classes(
                                    "rounded-control border border-border bg-panel-2 px-2.5 py-1 text-[13px] "
                                    "font-semibold text-text"
                                ).mark("search-sort")

                        chips = active_filter_chips(state.filters, state.facets)
                        if chips:
                            with ui.row().classes("mb-3 w-full flex-wrap items-center gap-2").mark("search-chips"):
                                for index, chip in enumerate(chips):
                                    ui.button(
                                        chip.label,
                                        on_click=lambda c=chip: replace_filters(c.without),
                                    ).props("flat dense no-caps rounded icon-right=close").classes(
                                        "rounded-full bg-accent-soft px-3 py-0.5 text-[13px] font-semibold text-accent"
                                    ).mark(f"search-chip-{index}")

                        with ui.row().classes(
                            "mb-4 w-full flex-wrap items-center gap-3 rounded-control bg-ai-bubble px-4 py-3"
                        ):
                            ui.icon("auto_awesome", size="20px").classes("text-accent")
                            ui.label(t("search.askAi")).classes("min-w-0 flex-1 text-[13px] text-text")
                            ui.link(t("search.askAiButton"), "/").classes(
                                "rounded-control bg-panel px-3 py-1.5 text-[13px] font-semibold text-accent no-underline"
                            )

                    results_header()

                    @ui.refreshable
                    def results_body() -> None:
                        grid_ref["row"] = None
                        message = None
                        if state.is_loading and not state.cars:
                            message = t("search.loading")
                        elif state.error:
                            message = t("search.error")
                        elif not state.cars:
                            message = t("search.empty")
                        if message is not None:
                            ui.label(message).classes(
                                "w-full rounded-card border border-dashed border-border px-5 py-10 text-center "
                                "text-[13px] text-subtext"
                            ).mark("search-message")
                            return
                        grid_ref["row"] = results_grid(
                            state.cars,
                            lambda car: open_detail(car.configuration_id),
                            False,
                            None,
                            None,
                            compare_toggles,
                        )

                    results_body()

                    @ui.refreshable
                    def loading_more() -> None:
                        if state.is_loading_more:
                            with ui.row().classes("mt-4 w-full items-center justify-center gap-2"):
                                ui.spinner(size="1.25rem")
                                ui.label(t("results.loadingMore")).classes("text-[13px] text-subtext")

                    loading_more()

            @ui.refreshable
            def compare_tray() -> None:
                items = compare_state.items
                if not items:
                    return
                with ui.row().classes(
                    "w-full shrink-0 flex-nowrap items-center justify-between gap-3 border-t border-border bg-panel "
                    "px-4 py-2.5 md:px-7"
                ):
                    ui.label(t("compare.trayCount", count=len(items))).classes("text-[13px] font-semibold text-text")
                    with ui.row().classes("shrink-0 flex-nowrap items-center gap-2"):
                        ui.button(t("compare.clear"), on_click=clear_comparison).props("flat dense no-caps").classes(
                            "text-[12.5px] text-subtext"
                        )
                        ui.button(
                            t("compare.open", count=len(items)), icon="compare_arrows", on_click=start_comparison
                        ).props("no-caps unelevated").classes(
                            "rounded-control bg-accent px-3 py-1.5 text-[13px] font-semibold text-accent-text"
                        )

            compare_tray()

            @ui.refreshable
            def mobile_bar() -> None:
                """Phones only: switches between the filters and the results."""
                with ui.row().classes(
                    "w-full shrink-0 border-t border-border bg-panel px-4 pt-2.5 "
                    "pb-[calc(10px+env(safe-area-inset-bottom))] md:hidden!"
                ):
                    if mobile["filters_open"]:
                        ui.button(
                            t_count("search.showResults", state.total), on_click=lambda: set_mobile_filters(False)
                        ).props("no-caps unelevated").classes(
                            "w-full rounded-control bg-accent py-2.5 text-[15px] font-bold text-accent-text"
                        ).mark("mobile-show-results")
                    else:
                        count = len(active_filter_chips(state.filters, state.facets))
                        ui.button(
                            f"{t('search.filtersTitle')} ({count})",
                            icon="tune",
                            on_click=lambda: set_mobile_filters(True),
                        ).props("flat no-caps").classes(
                            "w-full rounded-control border border-border bg-panel-2 py-2.5 text-[14px] font-semibold "
                            "text-text"
                        ).mark("mobile-show-filters")

            mobile_bar()

        try:
            await ui.context.client.connected()
        except TimeoutError:
            return
        await state.load_facets()
        sidebar.refresh()
        await state.search()
        refresh_results()
