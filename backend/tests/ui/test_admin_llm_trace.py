"""Smoke-tests the admin console's "AI komunikace" tab
(app/ui/components/llm_trace_panel.py) against the process-wide
`trace_log`, filled directly instead of through a real AI call.
"""

from datetime import datetime
from pathlib import Path

import pytest
from nicegui import ui
from nicegui.testing import User

from app.ai.trace import llm_purpose, trace_log

pytestmark = [
    pytest.mark.usefixtures("patch_ui_session"),
    pytest.mark.nicegui_main_file(str(Path(__file__).with_name("_user_main.py"))),
]


@pytest.fixture(autouse=True)
def _empty_trace_log():
    trace_log.clear()
    yield
    trace_log.clear()


def _record_groq_call() -> None:
    with llm_purpose("requirement_extraction"):
        trace_log.record(
            started_at=datetime.now().astimezone(),
            provider="groq",
            model="openai/gpt-oss-120b",
            request={
                "model": "openai/gpt-oss-120b",
                "max_tokens": 1024,
                "messages": [
                    {"role": "system", "content": "SYSTEM-PROMPT-MARKER"},
                    {"role": "user", "content": "Hledám rodinné SUV"},
                ],
            },
            response={"id": "chatcmpl-1", "choices": []},
            reply_text='{"requirements": {}}',
            duration_ms=812.4,
            input_tokens=420,
            output_tokens=69,
        )


async def test_admin_sees_traced_groq_call(user: User, log_in) -> None:
    _record_groq_call()
    await user.open("/")
    await log_in(user, "boss@example.cz", admin=True)

    await user.open("/admin")
    user.find("AI komunikace").click()

    await user.should_see("1 volání · 0 chyb · 489 tokenů")
    await user.should_see("Extrakce požadavků · groq/openai/gpt-oss-120b", retries=20)


async def test_opening_an_entry_shows_the_exchange(user: User, log_in) -> None:
    _record_groq_call()
    await user.open("/")
    await log_in(user, "boss@example.cz", admin=True)
    await user.open("/admin")
    user.find("AI komunikace").click()

    # The test simulation's click() doesn't toggle an expansion; setting
    # its value fires the same on_value_change the browser would.
    for expansion in user.find(kind=ui.expansion).elements:
        expansion.set_value(True)

    await user.should_see("SYSTEM-PROMPT-MARKER")
    await user.should_see("Hledám rodinné SUV")


async def test_clear_empties_the_trace(user: User, log_in) -> None:
    _record_groq_call()
    await user.open("/")
    await log_in(user, "boss@example.cz", admin=True)
    await user.open("/admin")
    user.find("AI komunikace").click()

    user.find("Vymazat").click()

    await user.should_see("Zatím žádné volání")
    assert trace_log.entries() == []


async def test_non_admins_never_get_the_trace(user: User) -> None:
    _record_groq_call()
    await user.open("/admin")

    await user.should_not_see("AI komunikace")
    await user.should_not_see("Hledám rodinné SUV")
