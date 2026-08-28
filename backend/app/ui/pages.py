"""The app's single page - port of frontend/src/pages/ChatPage.tsx (plus
`App.tsx`/`main.tsx`, which had nothing else to port: no router, no other
routed screens).
"""

from dataclasses import dataclass

from nicegui import app, ui

from app.models.enums import Drivetrain, FuelType
from app.schemas.vehicle import VehicleSummary
from app.ui.components.chat_column import chat_column
from app.ui.components.filter_bar import filter_bar
from app.ui.components.header import app_header
from app.ui.components.requirements_drawer import requirements_drawer
from app.ui.components.results_grid import results_grid, sort_control
from app.ui.components.vehicle_detail_modal import vehicle_detail_modal
from app.ui.i18n import t, t_count
from app.ui.sort import BACKEND_SORT_OPTIONS, sort_cars
from app.ui.state import CatalogState, ConversationState
from app.ui.styles import register_styles

CUSTOM_ORDER_KEY = "custom_car_order"


@dataclass
class _SortState:
    """Page-local UI state that never needs to survive a restart - the
    direct analogue of `ChatPage`'s own `useState`s (not modeled in
    `ConversationState`/`CatalogState`, which are the ported Zustand
    stores).
    """

    option: str = "recommended"


@ui.page("/")
async def index() -> None:
    """Builds the whole app for one browser connection - NiceGUI gives
    each connection its own call of this function with private local
    state (see `app/ui/state.py`'s module docstring), the direct analogue
    of one mounted React tree.

    Event handlers are all defined before any UI is built: the
    refreshable render functions built further down (`chrome`/`results`/
    `drawer`) are invoked once immediately, synchronously, to draw the
    initial page - and their bodies pass these handlers to child
    components as plain values (button callbacks), which requires the
    names to already be bound. The handlers' own bodies are free to
    reference `chrome`/`results`/`drawer`/`chat_refresh` even though
    those are defined later, since a handler body only actually runs
    later too (on a click, well after page construction has finished).
    """
    register_styles()

    conv = ConversationState()
    catalog_state = CatalogState()
    sort_state = _SortState()

    def custom_order() -> list[int]:
        return app.storage.user.get(CUSTOM_ORDER_KEY, [])

    def backend_sort() -> str | None:
        if conv.has_narrowed:
            return None
        return sort_state.option if sort_state.option in BACKEND_SORT_OPTIONS else None

    def displayed_cars() -> list[VehicleSummary]:
        base_cars = conv.cars if conv.has_narrowed else catalog_state.cars
        client_sort = (
            "custom" if sort_state.option == "custom" else (sort_state.option if conv.has_narrowed else "recommended")
        )
        return sort_cars(base_cars, client_sort, custom_order())

    open_detail = vehicle_detail_modal()

    def refresh_all() -> None:
        chrome.refresh()
        results.refresh()
        drawer.refresh()
        chat_refresh()

    async def send(text: str) -> None:
        await conv.send(text)
        refresh_all()

    async def restart() -> None:
        await conv.restart()
        await catalog_state.load_first_page(backend_sort())
        refresh_all()

    async def toggle_drawer() -> None:
        conv.toggle_drawer()
        drawer.refresh()

    async def close_drawer() -> None:
        conv.close_drawer()
        drawer.refresh()

    async def change_sort(value: str) -> None:
        sort_state.option = value
        if not conv.has_narrowed and value in BACKEND_SORT_OPTIONS:
            await catalog_state.load_first_page(value)
        results.refresh()

    async def load_more() -> None:
        await catalog_state.load_more(backend_sort())
        results.refresh()

    async def change_brand(brand_id: int | None) -> None:
        catalog_state.brand_id = brand_id
        await catalog_state.load_first_page(backend_sort())
        results.refresh()

    async def change_fuel_type(fuel_type: FuelType | None) -> None:
        catalog_state.fuel_type = fuel_type
        await catalog_state.load_first_page(backend_sort())
        results.refresh()

    async def change_drivetrain(drivetrain: Drivetrain | None) -> None:
        catalog_state.drivetrain = drivetrain
        await catalog_state.load_first_page(backend_sort())
        results.refresh()

    def reorder(order: list[int]) -> None:
        app.storage.user[CUSTOM_ORDER_KEY] = order
        results.refresh()

    with ui.column().classes("relative flex h-screen w-full flex-col overflow-hidden bg-bg text-text gap-0"):

        @ui.refreshable
        def chrome() -> None:
            app_header(len(conv.requirements), restart, toggle_drawer)

        chrome()

        with ui.row().classes("relative flex min-h-0 flex-1 w-full gap-0"):
            chat_refresh = chat_column(conv, send)

            with ui.column().classes("min-w-0 h-full flex-1 overflow-y-auto px-7 py-6 gap-0"):

                @ui.refreshable
                def results() -> None:
                    cars = displayed_cars()
                    has_results = len(cars) > 0
                    show_catalog_error = not conv.has_narrowed and catalog_state.error and not has_results
                    show_catalog_loading = not conv.has_narrowed and catalog_state.is_loading

                    with ui.row().classes("mb-4.5 w-full flex-wrap items-start justify-between gap-3"):
                        with ui.column().classes("gap-0"):
                            title = (
                                t_count("results.title", len(cars))
                                if conv.has_narrowed
                                else t_count("results.browsingTitle", len(cars))
                            )
                            ui.label(title).classes("text-[19px] font-bold text-text")
                            ui.label(t("results.updated") if conv.has_narrowed else t("results.startPrompt")).classes(
                                "mt-0.5 text-[13px] text-subtext"
                            )
                        sort_control(sort_state.option, change_sort)

                    if not conv.has_narrowed:
                        filter_bar(
                            catalog_state.brands,
                            catalog_state.brand_id,
                            catalog_state.fuel_type,
                            catalog_state.drivetrain,
                            change_brand,
                            change_fuel_type,
                            change_drivetrain,
                        )

                    if conv.error is not None:
                        message = t("chat.aiNotConfigured") if conv.error == "ai_not_configured" else t("chat.genericError")
                        ui.label(message).classes(
                            "mb-4 w-full rounded-control bg-flag-bg px-3.5 py-2.5 text-[13px] text-flag"
                        )

                    if show_catalog_loading:
                        ui.label(t("results.loadingCatalog")).classes(
                            "w-full px-5 py-10 text-center text-[13px] text-subtext"
                        )
                    elif show_catalog_error:
                        ui.label(t("results.catalogError")).classes(
                            "w-full px-5 py-10 text-center text-[13px] text-subtext"
                        )
                    else:
                        reorderable = sort_state.option == "custom"
                        results_grid(
                            cars,
                            lambda car: open_detail(car.configuration_id),
                            reorderable,
                            reorder if reorderable else None,
                        )
                        if not conv.has_narrowed and catalog_state.has_more:
                            with ui.row().classes("mt-4 w-full justify-center"):
                                ui.button(
                                    t("results.loadingMore") if catalog_state.is_loading_more else t("results.loadMore"),
                                    on_click=load_more,
                                ).props("flat no-caps").classes(
                                    "rounded-control border border-border bg-panel-2 px-4 py-2 text-[13px] "
                                    "font-semibold text-text"
                                )

                results()

            @ui.refreshable
            def drawer() -> None:
                requirements_drawer(conv.requirements, conv.drawer_open, close_drawer)

            drawer()

    await conv.begin()
    await catalog_state.load_brands()
    await catalog_state.load_first_page(backend_sort())
    refresh_all()
