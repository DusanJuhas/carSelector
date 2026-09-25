"""Wizard step 7 (annual mileage) through NiceGUI's `user` fixture: the
input starts at a typical value and its arrows move by 1000 km."""

import asyncio
from pathlib import Path

import pytest
from nicegui import ui
from nicegui.testing import User

from app.ui.components.wizard import ANNUAL_KM_STEP, DEFAULT_ANNUAL_KM

pytestmark = [
    pytest.mark.usefixtures("patch_ui_session"),
    pytest.mark.nicegui_main_file(str(Path(__file__).with_name("_user_main.py"))),
]


async def _open_step_7(user: User) -> ui.number:
    await user.open("/")
    user.find("Průvodce výběrem").click()
    await user.should_see("Otázka 1 z", retries=100)
    for step in range(2, 8):
        user.find("Nevím / přeskočit").click()
        await user.should_see(f"Otázka {step} z", retries=100)
    await asyncio.sleep(0)
    (field,) = user.find(marker="mileage-input").elements
    return field


async def test_mileage_starts_at_typical_value_with_1000_km_step(user: User) -> None:
    field = await _open_step_7(user)

    assert field.value == DEFAULT_ANNUAL_KM
    assert field.props["step"] == ANNUAL_KM_STEP
