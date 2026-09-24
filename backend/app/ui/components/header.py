"""Port of frontend/src/components/AppHeader.tsx."""

from collections.abc import Callable

from nicegui import ui

from app.schemas.auth import UserRead
from app.ui.i18n import t


def app_header(
    requirements_count: int,
    on_restart: Callable[[], None],
    on_toggle_drawer: Callable[[], None],
    on_open_wizard: Callable[[], None],
    ai_configured: bool,
    on_open_api_key: Callable[[], None],
    user: UserRead | None,
    on_login: Callable[[], None],
    on_logout: Callable[[], None],
) -> None:
    """Builds the top bar: brand/tagline on the left, restart + wizard +
    requirements-drawer toggle and the login/logout control on the right.
    The admin link and the API-key button are rendered for admins only.

    On mobile (below `md`) the tagline is hidden, the requirements button
    shrinks to an icon + badge, and restart/login/admin/API-key fold into
    a dropdown behind a hamburger button.

    Args:
        requirements_count: Shown as a badge on the drawer-toggle button.
        on_restart: Called when "Restartovat" is clicked.
        on_toggle_drawer: Called when the requirements button is clicked.
        on_open_wizard: Called when "Průvodce výběrem" is clicked - opens
            the guided question-by-question alternative to the free-text
            chat (see `app/ui/components/wizard.py`).
        ai_configured: Whether an AI API key is set - switches the API-key
            button between its plain and "missing" (highlighted) look.
        on_open_api_key: Called when the API-key button is clicked - opens
            `app/ui/components/api_key_dialog.py`. Only ever shown to
            admins, since the key is process-wide.
        user: The logged-in user, or `None` if anonymous. Decides
            whether admin-only controls are shown - cosmetic only, the
            server-side checks live where the privileged actions do (see
            `app/ui/auth.py`).
        on_login: Called when "Přihlásit se" is clicked - opens
            `app/ui/components/login_dialog.py`.
        on_logout: Called when "Odhlásit" is clicked.
    """
    is_admin = user is not None and user.is_admin
    with ui.row().classes(
        "relative shrink-0 flex-nowrap items-center justify-between gap-3 border-b border-border "
        "px-4 py-3 md:px-7 md:py-4.5 w-full"
    ):
        with ui.column().classes("min-w-0 gap-0.5"):
            ui.label(t("header.brand")).classes("text-xl font-bold tracking-tight text-text")
            ui.label(t("header.tagline")).classes("text-[12.5px] text-subtext max-md:hidden!")

        with ui.row().classes("flex-nowrap items-center gap-2 md:gap-2.5"):
            # Always visible, on every screen size: the primary action and
            # the requirements badge. Everything else lives in `secondary`
            # below, which is an inline row on desktop but a hamburger-
            # toggled dropdown on mobile - the same elements either way (not
            # a duplicated mobile copy), so each control exists exactly once.
            ui.button(t("header.startWizard"), on_click=on_open_wizard).props("no-caps unelevated").classes(
                "rounded-control bg-accent px-3.5 py-2 text-[13px] font-semibold text-accent-text"
            )
            with ui.button(on_click=on_toggle_drawer).props("flat no-caps").classes(
                "flex items-center gap-2 rounded-control border border-border bg-panel-2 px-3.5 py-2 "
                "text-[13px] font-semibold text-text"
            ).tooltip(t("header.technicalRequirements")).mark("requirements-toggle"):
                ui.label(t("header.technicalRequirements")).classes("max-md:hidden!")
                ui.icon("tune", size="18px").classes("md:hidden!")
                ui.label(str(requirements_count)).classes(
                    "rounded-full bg-accent px-[7px] py-0.5 text-[11px] font-bold text-accent-text"
                )

            secondary = ui.row().classes(
                "items-center gap-2.5 "
                "max-md:absolute max-md:right-4 max-md:top-full max-md:z-30 max-md:mt-1 max-md:min-w-[220px] "
                "max-md:flex-col! max-md:items-stretch! max-md:gap-1.5! max-md:rounded-card max-md:border "
                "max-md:border-border max-md:bg-panel max-md:p-2 max-md:shadow-card max-md:hidden!"
            )

            def _toggle_menu() -> None:
                if "max-md:hidden!" in secondary.classes:
                    secondary.classes(remove="max-md:hidden!")
                else:
                    secondary.classes(add="max-md:hidden!")

            def _from_menu(action: Callable[[], None]) -> Callable[[], None]:
                """Wraps a menu item's handler so it also closes the mobile dropdown."""

                def _run():
                    secondary.classes(add="max-md:hidden!")
                    return action()

                return _run

            ui.button(icon="menu", on_click=_toggle_menu).props("flat round").classes(
                "text-text md:hidden!"
            ).tooltip(t("header.menu"))

            with secondary:
                if is_admin:
                    ui.link("Admin", "/admin").classes(
                        "text-[12.5px] text-subtext underline-offset-2 hover:underline touch-underline max-md:px-3.5 "
                        "max-md:py-2"
                    )
                    ui.button(
                        t("header.apiKey") if ai_configured else t("header.apiKeyMissing"),
                        icon="key",
                        on_click=_from_menu(on_open_api_key),
                    ).props("flat no-caps").classes(
                        "rounded-control border px-3.5 py-2 text-[13px] "
                        + ("border-border text-subtext" if ai_configured else "border-flag bg-flag-bg text-flag")
                    )
                ui.button(t("header.restart"), on_click=_from_menu(on_restart)).props("flat no-caps").classes(
                    "rounded-control border border-border px-3.5 py-2 text-[13px] text-subtext"
                )
                if user is None:
                    ui.button(t("header.login"), icon="login", on_click=_from_menu(on_login)).props(
                        "flat no-caps"
                    ).classes("rounded-control border border-border px-3.5 py-2 text-[13px] text-subtext")
                else:
                    ui.label(user.email).classes("text-[12.5px] text-subtext max-md:px-3.5 max-md:py-1 break-all")
                    ui.button(t("header.logout"), on_click=_from_menu(on_logout)).props("flat no-caps").classes(
                        "rounded-control border border-border px-3.5 py-2 text-[13px] text-subtext"
                    )
