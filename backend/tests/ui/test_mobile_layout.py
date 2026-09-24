"""Mobile layout (below the `md` breakpoint) through NiceGUI's headless
`user` fixture. There's no real viewport here - these check that the
mobile-only controls exist and flip the right CSS classes; what those
classes actually do at 375px is checked in a real browser.
"""

import asyncio
from pathlib import Path

import pytest
from nicegui import ui
from nicegui.testing import User

from app.ai import client as client_module
from app.ui.pages import MOBILE_HIDDEN

pytestmark = [
    pytest.mark.usefixtures("patch_ui_session"),
    pytest.mark.nicegui_main_file(str(Path(__file__).with_name("_user_main.py"))),
]


@pytest.fixture(autouse=True)
def _no_key(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(client_module, "AI_PROVIDER", "groq")
    monkeypatch.setattr(client_module, "GROQ_API_KEY", None)
    client_module.set_runtime_api_key(None)
    yield
    client_module.set_runtime_api_key(None)


def _classes(user: User, marker: str) -> list[str]:
    (element,) = user.find(marker=marker).elements
    return list(element.classes)


async def test_tab_bar_starts_on_chat_and_switches_to_results(user: User) -> None:
    await user.open("/")
    await user.should_see("Konverzace")
    await user.should_see("Výsledky (")

    assert MOBILE_HIDDEN not in _classes(user, "chat-panel")
    assert MOBILE_HIDDEN in _classes(user, "results-panel")

    user.find(kind=ui.button, content="Výsledky (").click()

    assert MOBILE_HIDDEN in _classes(user, "chat-panel")
    assert MOBILE_HIDDEN not in _classes(user, "results-panel")

    user.find(kind=ui.button, content="Konverzace").click()

    assert MOBILE_HIDDEN not in _classes(user, "chat-panel")
    assert MOBILE_HIDDEN in _classes(user, "results-panel")


async def test_sort_and_filters_toggle_open_on_mobile(user: User) -> None:
    await user.open("/")
    # The catalog loads after first paint and rebuilds the results header -
    # wait for that, or the click lands on a header about to be replaced.
    await user.should_see("v katalogu", retries=100)
    assert MOBILE_HIDDEN in _classes(user, "sort-controls")

    user.find("Řazení a filtry").click()

    # The toggle rebuilds the results header via `refreshable.refresh()`,
    # which lands on a later event-loop tick.
    for _ in range(50):
        if MOBILE_HIDDEN not in _classes(user, "sort-controls"):
            break
        await asyncio.sleep(0.02)
    assert MOBILE_HIDDEN not in _classes(user, "sort-controls")


async def test_header_keeps_secondary_actions_behind_menu_button(user: User) -> None:
    await user.open("/")
    # Each control exists once (not a duplicated mobile copy) - `find`
    # would otherwise match two buttons and the click would fail.
    user.find("Restartovat").click()
    await user.should_see("Přihlásit se")
    await user.should_see("menu")


async def test_requirements_drawer_has_close_button(user: User) -> None:
    await user.open("/")
    user.find(marker="requirements-toggle").click()
    await user.should_see("Zatím nebyly zachyceny žádné požadavky.")
    user.find(kind=ui.button, content="Zavřít").click()
