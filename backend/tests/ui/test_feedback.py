"""User feedback end to end, through NiceGUI's headless `user` fixture:
sending it from the account menu, and an admin resolving it on the admin
console's "Zpětná vazba" tab.
"""

import asyncio
from pathlib import Path

import pytest
from nicegui.testing import User
from sqlalchemy.orm import Session

from app.models.feedback import Feedback

pytestmark = [
    pytest.mark.usefixtures("patch_ui_session"),
    pytest.mark.nicegui_main_file(str(Path(__file__).with_name("_user_main.py"))),
]


def _set(user: User, marker: str, value: object) -> None:
    """Sets a value element directly - the simulated `type()` doesn't reach
    a radio group or a select."""
    for element in user.find(marker=marker).elements:
        element.value = value


async def _wait_for(condition, tries: int = 100) -> bool:
    for _ in range(tries):
        if condition():
            return True
        await asyncio.sleep(0.02)
    return False


async def test_anonymous_user_is_not_offered_feedback(user: User) -> None:
    await user.open("/")
    await user.should_see(marker="login")
    await user.should_not_see(marker="menu-feedback")


async def test_user_sends_feedback_and_admin_resolves_it(user: User, log_in, patch_ui_session: Session) -> None:
    await user.open("/")
    await log_in(user, "jana@example.cz")

    user.find(marker="menu-feedback").click()
    await user.should_see("Napsat zpětnou vazbu", retries=100)
    user.find(marker="feedback-text").type("Cena u Octavie nesedí s ceníkem.")
    user.find(marker="feedback-submit").click()
    await user.should_see("Vyberte prosím, o co jde", retries=100)

    _set(user, "feedback-type", "bug")
    user.find(marker="feedback-submit").click()
    await user.should_see(marker="feedback-sent", retries=100)

    item = patch_ui_session.query(Feedback).one()
    assert (item.type, item.status, item.language) == ("bug", "new", "cs")
    assert '"page":"search"' in item.context_json

    user.find(marker="logout").click()
    await user.open("/")
    await log_in(user, "boss@example.cz", admin=True)
    await user.open("/admin")
    await user.should_see("Zpětná vazba (1)")
    user.find(marker="feedback-tab").click()
    await user.should_see("Cena u Octavie nesedí s ceníkem.", retries=100)
    await user.should_see("Odesláno z: výběr auta", retries=100)

    _set(user, "feedback-status", "resolved")
    user.find(marker="feedback-note").type("Opraveno v importu.")
    user.find(marker="feedback-save").click()

    assert await _wait_for(lambda: (patch_ui_session.refresh(item), item.status)[1] == "resolved")
    assert item.admin_note == "Opraveno v importu."
