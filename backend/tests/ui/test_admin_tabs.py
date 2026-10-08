"""Smoke-tests the admin console's tab split: "Data" lists the sources only,
the scraper/import job controls live on their own "Ovládání" tab.
"""

from pathlib import Path

import pytest
from nicegui.testing import User

pytestmark = [
    pytest.mark.usefixtures("patch_ui_session"),
    pytest.mark.nicegui_main_file(str(Path(__file__).with_name("_user_main.py"))),
]


async def test_job_controls_are_on_their_own_tab(user: User, log_in) -> None:
    await user.open("/")
    await log_in(user, "boss@example.cz", admin=True)

    await user.open("/admin")
    await user.should_see("Zdroje (config/sources.yaml)")

    user.find("Ovládání").click()
    await user.should_see("1. Spustit scraper")
    await user.should_see("2. Naimportovat do katalogu")
