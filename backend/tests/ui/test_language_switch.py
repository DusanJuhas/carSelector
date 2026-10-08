"""The header's CS/EN toggle: switches the whole page (and the assistant's
greeting) to English, remembers the choice for the browser, and switches
back.
"""

from pathlib import Path

import pytest
from nicegui import ui
from nicegui.testing import User

pytestmark = [
    pytest.mark.usefixtures("patch_ui_session"),
    pytest.mark.nicegui_main_file(str(Path(__file__).with_name("_user_main.py"))),
]


async def test_language_toggle_switches_to_english_and_back(user: User) -> None:
    await user.open("/")
    await user.should_see("Průvodce výběrem")

    user.find(marker="language-toggle", kind=ui.button).click()
    await user.should_see("Selection guide", retries=50)
    await user.should_see("Hi! Tell me how you'll use your new car", retries=50)
    await user.should_not_see("Průvodce výběrem")

    # Remembered for the browser, not just this page load.
    await user.open("/")
    await user.should_see("Selection guide", retries=50)

    user.find(marker="language-toggle", kind=ui.button).click()
    await user.should_see("Průvodce výběrem", retries=50)
