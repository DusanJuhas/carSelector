"""Covers app/ui/state.py's ConversationState/CatalogState against the
real service layer + seeded in-memory DB (via `patch_ui_session` -
see conftest.py). Exercises the same "browsing mode load", "AI not
configured", and "restart" paths verified manually in-browser during the
NiceGUI migration, as an automated regression net - not a NiceGUI
`User`-fixture test: those need a `main_file` containing a literal
`ui.run()` call (per NiceGUI 3.x's testing docs), which doesn't fit this
app's `ui.run_with(app, ...)`-mounted-on-FastAPI structure, so this
exercises the state layer directly instead - the layer that actually
talks to the database/orchestrator and carries the real risk, independent
of how the DOM ends up rendering it.
"""

from app.ui.state import CatalogState, ConversationState
from tests.conftest import SeededData


async def test_catalog_state_loads_seeded_vehicles(patch_ui_session, seeded_session: SeededData) -> None:
    state = CatalogState()
    await state.load_first_page(sort=None)
    assert state.total == 2
    assert len(state.cars) == 2
    assert not state.error


async def test_catalog_state_has_more_is_false_once_fully_loaded(patch_ui_session, seeded_session: SeededData) -> None:
    state = CatalogState(page_size=20)
    await state.load_first_page(sort=None)
    assert state.has_more is False


async def test_catalog_state_load_more_is_a_noop_when_nothing_left(patch_ui_session, seeded_session: SeededData) -> None:
    state = CatalogState()
    await state.load_first_page(sort=None)
    cars_before = list(state.cars)
    await state.load_more(sort=None)
    assert state.cars == cars_before


async def test_conversation_state_begin_starts_and_seeds_intro_message(patch_ui_session) -> None:
    state = ConversationState()
    await state.begin()
    assert state.conversation_id is not None
    assert len(state.messages) == 1
    assert state.messages[0][0] == "assistant"
    assert not state.is_loading


async def test_conversation_state_send_without_api_key_sets_ai_not_configured(patch_ui_session) -> None:
    # No ANTHROPIC_API_KEY in the test environment - see app/ai/client.py
    # and backend/README.md's "degrades to a 503 ai_not_configured
    # response" note, exercised here the same way the API test suite
    # exercises it for the REST endpoint.
    state = ConversationState()
    await state.begin()
    await state.send("Chci rodinné auto do 900 tisíc.")
    assert state.error == "ai_not_configured"
    assert not state.is_sending
    # The user's message still landed in the transcript even though the
    # AI call failed - matches ChatColumn's behavior of showing what was
    # sent regardless of the response outcome.
    assert state.messages[-1] == ("user", "Chci rodinné auto do 900 tisíc.")


async def test_conversation_state_send_ignores_blank_text(patch_ui_session) -> None:
    state = ConversationState()
    await state.begin()
    message_count = len(state.messages)
    await state.send("   ")
    assert len(state.messages) == message_count


async def test_conversation_state_restart_resets_and_begins_again(patch_ui_session) -> None:
    state = ConversationState()
    await state.begin()
    first_id = state.conversation_id
    state.drawer_open = True

    await state.restart()

    assert state.conversation_id is not None
    assert state.conversation_id != first_id
    assert state.drawer_open is False
    assert state.has_narrowed is False
    assert len(state.messages) == 1


def test_conversation_state_toggle_and_close_drawer() -> None:
    state = ConversationState()
    assert state.drawer_open is False
    state.toggle_drawer()
    assert state.drawer_open is True
    state.close_drawer()
    assert state.drawer_open is False
