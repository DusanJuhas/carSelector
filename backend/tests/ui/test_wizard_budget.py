"""Wizard step 1 (budget) through NiceGUI's `user` fixture: the input starts
at a typical price and its arrows move by 50 000 Kč."""

import asyncio
from pathlib import Path

import pytest
from nicegui import ui
from nicegui.testing import User

from app.ui.components.wizard import BUDGET_STEP, DEFAULT_BUDGET

pytestmark = [
    pytest.mark.usefixtures("patch_ui_session"),
    pytest.mark.nicegui_main_file(str(Path(__file__).with_name("_user_main.py"))),
]


async def _open_step_1(user: User) -> ui.number:
    await user.open("/")
    user.find("Průvodce výběrem").click()
    await user.should_see("Otázka 1 z", retries=100)
    await asyncio.sleep(0)
    (field,) = user.find(marker="budget-input").elements
    return field


async def test_budget_starts_at_typical_price_with_50000_step(user: User) -> None:
    field = await _open_step_1(user)

    assert field.value == DEFAULT_BUDGET
    assert field.props["step"] == BUDGET_STEP
