"""Port of frontend/src/components/AppHeader.tsx."""

from collections.abc import Callable

from nicegui import ui

from app.ui.i18n import t


def app_header(requirements_count: int, on_restart: Callable[[], None], on_toggle_drawer: Callable[[], None]) -> None:
    """Builds the top bar: brand/tagline on the left, restart + requirements-drawer toggle on the right.

    Args:
        requirements_count: Shown as a badge on the drawer-toggle button.
        on_restart: Called when "Restartovat" is clicked.
        on_toggle_drawer: Called when the requirements button is clicked.
    """
    with ui.row().classes("shrink-0 items-center justify-between border-b border-border px-7 py-4.5 w-full"):
        with ui.column().classes("gap-0.5"):
            ui.label(t("header.brand")).classes("text-xl font-bold tracking-tight text-text")
            ui.label(t("header.tagline")).classes("text-[12.5px] text-subtext")

        with ui.row().classes("items-center gap-2.5"):
            ui.button(t("header.restart"), on_click=on_restart).props("flat no-caps").classes(
                "rounded-control border border-border px-3.5 py-2 text-[13px] text-subtext"
            )
            with ui.button(on_click=on_toggle_drawer).props("flat no-caps").classes(
                "flex items-center gap-2 rounded-control border border-border bg-panel-2 px-3.5 py-2 "
                "text-[13px] font-semibold text-text"
            ):
                ui.label(t("header.technicalRequirements"))
                ui.label(str(requirements_count)).classes(
                    "rounded-full bg-accent px-[7px] py-0.5 text-[11px] font-bold text-accent-text"
                )
