"""The detail dialog's "Odkazy" section through NiceGUI's `user` fixture:
manufacturer website and YouTube review links for the shown model."""

from pathlib import Path

import pytest
from nicegui import ui
from nicegui.testing import User

from tests.conftest import SeededData

pytestmark = [
    pytest.mark.usefixtures("patch_ui_session"),
    pytest.mark.nicegui_main_file(str(Path(__file__).with_name("_user_main.py"))),
]


async def test_detail_dialog_shows_external_links(user: User, seeded_session: SeededData) -> None:
    await user.open("/")
    await user.should_see("v katalogu", retries=100)

    user.find(marker=f"car-{seeded_session.config_rline_awd_id}").click()
    await user.should_see("Web výrobce", retries=100)
    await user.should_see("Video recenze")

    (manufacturer,) = user.find(marker="link-manufacturer").elements
    (review,) = user.find(marker="link-review-video").elements
    assert isinstance(manufacturer, ui.link)
    assert manufacturer.props["href"] == "https://www.volkswagen.cz"
    assert manufacturer.props["target"] == "_blank"
    assert review.props["href"] == "https://www.youtube.com/results?search_query=Volkswagen+Tiguan+recenze"
