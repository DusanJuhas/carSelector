"""The like (heart) button on result cards, through NiceGUI's headless
`user` fixture. The seeded catalog has two cards per model (see
`app/db/seed.py`), which is what makes "one like fills every card of the
model" observable here.
"""

import asyncio
from pathlib import Path

import pytest
from nicegui.testing import User
from sqlalchemy.orm import Session

from app.ai import client as client_module
from app.models.user import User as UserRow
from app.services import liked_models
from tests.conftest import SeededData

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


def _icons(user: User, model_id: int) -> list[str]:
    return [button.props.get("icon") for button in user.find(marker=f"like-{model_id}").elements]


async def _wait_for_icons(user: User, model_id: int, icon: str) -> list[str]:
    """The toggle awaits a DB write before updating the buttons - poll."""
    for _ in range(100):
        icons = _icons(user, model_id)
        if icons and all(i == icon for i in icons):
            break
        await asyncio.sleep(0.02)
    return _icons(user, model_id)


async def _open_catalog(user: User) -> None:
    await user.open("/")
    await user.should_see("v katalogu", retries=100)


def _account_id(session: Session, email: str) -> int:
    return session.query(UserRow).filter(UserRow.email == email).one().id


async def test_anonymous_like_fills_every_card_of_the_model(user: User, seeded_session: SeededData) -> None:
    await _open_catalog(user)
    vw = seeded_session.vw_model_id
    assert _icons(user, vw) == ["favorite_border", "favorite_border"]

    user.find(marker=f"like-{vw}").click()

    assert await _wait_for_icons(user, vw, "favorite") == ["favorite", "favorite"]
    assert _icons(user, seeded_session.model_id) == ["favorite_border", "favorite_border"]


async def test_second_click_unlikes(user: User, seeded_session: SeededData) -> None:
    await _open_catalog(user)
    vw = seeded_session.vw_model_id

    user.find(marker=f"like-{vw}").click()
    await _wait_for_icons(user, vw, "favorite")
    user.find(marker=f"like-{vw}").click()

    assert await _wait_for_icons(user, vw, "favorite_border") == ["favorite_border", "favorite_border"]


async def test_logged_in_like_is_saved_to_the_account_and_survives_reload(
    user: User, log_in, seeded_session: SeededData
) -> None:
    await _open_catalog(user)
    await log_in(user, "jana@example.cz")
    vw = seeded_session.vw_model_id

    user.find(marker=f"like-{vw}").click()
    await _wait_for_icons(user, vw, "favorite")

    account = _account_id(seeded_session.session, "jana@example.cz")
    assert liked_models.list_ids(seeded_session.session, account) == {vw}

    await _open_catalog(user)
    assert await _wait_for_icons(user, vw, "favorite") == ["favorite", "favorite"]


async def test_anonymous_likes_are_merged_into_the_account_on_login(
    user: User, log_in, seeded_session: SeededData
) -> None:
    await _open_catalog(user)
    vw = seeded_session.vw_model_id
    user.find(marker=f"like-{vw}").click()
    await _wait_for_icons(user, vw, "favorite")

    await log_in(user, "petr@example.cz")

    account = _account_id(seeded_session.session, "petr@example.cz")
    for _ in range(100):
        if liked_models.list_ids(seeded_session.session, account):
            break
        await asyncio.sleep(0.02)
    assert liked_models.list_ids(seeded_session.session, account) == {vw}


async def test_logout_clears_the_accounts_hearts(user: User, log_in, seeded_session: SeededData) -> None:
    await _open_catalog(user)
    await log_in(user, "eva@example.cz")
    vw = seeded_session.vw_model_id
    user.find(marker=f"like-{vw}").click()
    await _wait_for_icons(user, vw, "favorite")

    user.find("Odhlásit").click()

    assert await _wait_for_icons(user, vw, "favorite_border") == ["favorite_border", "favorite_border"]
