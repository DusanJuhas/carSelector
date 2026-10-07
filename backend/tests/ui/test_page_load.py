"""Regression test for the main page's build vs. NiceGUI's
`response_timeout` (3 s): slow startup loads - e.g. a logged-in user's
saved result being re-explained by the AI - must happen after the page is
sent, not before, or the visitor gets a "500 Server error" page.
"""

import asyncio
from pathlib import Path

import pytest
from nicegui.testing import User

from app.ui.state import ConversationState

pytestmark = [
    pytest.mark.usefixtures("patch_ui_session"),
    pytest.mark.nicegui_main_file(str(Path(__file__).with_name("_user_main.py"))),
]


async def test_slow_startup_load_does_not_time_out_the_page(user: User, monkeypatch: pytest.MonkeyPatch) -> None:
    original_begin = ConversationState.begin

    async def slow_begin(self: ConversationState) -> None:
        await asyncio.sleep(3.5)  # longer than NiceGUI's 3 s response_timeout
        await original_begin(self)

    monkeypatch.setattr(ConversationState, "begin", slow_begin)

    await user.open("/")  # raised on the 500 before the fix

    await user.should_see("Katalog vozů")  # loading state, not "0 vozů v katalogu"
    await user.should_see("v katalogu", retries=100)
