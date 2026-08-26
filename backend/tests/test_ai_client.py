"""Covers app/ai/client.py's provider selection and the two app/ai/llm.py
adapters. Uses fake API objects throughout - no real network calls, no
API key required to run this suite.
"""

from types import SimpleNamespace

import pytest

from app.ai import client as client_module
from app.ai.llm import AnthropicLlmClient, GroqLlmClient


@pytest.fixture(autouse=True)
def _clear_client_cache():
    """get_client() is @lru_cache(maxsize=1) - clear it before and after
    every test so one test's provider choice can't leak into the next.
    """
    client_module.get_client.cache_clear()
    yield
    client_module.get_client.cache_clear()


def test_get_client_raises_without_anthropic_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(client_module, "AI_PROVIDER", "anthropic")
    monkeypatch.setattr(client_module, "ANTHROPIC_API_KEY", None)
    with pytest.raises(RuntimeError, match="ANTHROPIC_API_KEY"):
        client_module.get_client()


def test_get_client_raises_without_groq_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(client_module, "AI_PROVIDER", "groq")
    monkeypatch.setattr(client_module, "GROQ_API_KEY", None)
    with pytest.raises(RuntimeError, match="GROQ_API_KEY"):
        client_module.get_client()


def test_get_client_raises_for_unknown_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(client_module, "AI_PROVIDER", "openai")
    with pytest.raises(RuntimeError, match="openai"):
        client_module.get_client()


def test_get_client_returns_anthropic_client_when_selected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(client_module, "AI_PROVIDER", "anthropic")
    monkeypatch.setattr(client_module, "ANTHROPIC_API_KEY", "sk-ant-fake")
    assert isinstance(client_module.get_client(), AnthropicLlmClient)


def test_get_client_returns_groq_client_when_selected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(client_module, "AI_PROVIDER", "groq")
    monkeypatch.setattr(client_module, "GROQ_API_KEY", "gsk-fake")
    assert isinstance(client_module.get_client(), GroqLlmClient)


def test_anthropic_llm_client_extracts_text_from_content_blocks() -> None:
    fake_response = SimpleNamespace(
        content=[
            SimpleNamespace(type="text", text="hello "),
            SimpleNamespace(type="text", text="world"),
        ]
    )
    calls = []

    class FakeMessages:
        def create(self, **kwargs):
            calls.append(kwargs)
            return fake_response

    fake_client = SimpleNamespace(messages=FakeMessages())
    llm = AnthropicLlmClient(fake_client, model="claude-test")

    result = llm.complete(system="sys", user_content="hi", max_tokens=50)

    assert result == "hello world"
    assert calls == [
        {
            "model": "claude-test",
            "max_tokens": 50,
            "system": "sys",
            "messages": [{"role": "user", "content": "hi"}],
        }
    ]


def test_groq_llm_client_extracts_message_content() -> None:
    fake_response = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content="hello from groq"))]
    )
    calls = []

    class FakeCompletions:
        def create(self, **kwargs):
            calls.append(kwargs)
            return fake_response

    fake_client = SimpleNamespace(chat=SimpleNamespace(completions=FakeCompletions()))
    llm = GroqLlmClient(fake_client, model="llama-test")

    result = llm.complete(system="sys", user_content="hi", max_tokens=50)

    assert result == "hello from groq"
    assert calls == [
        {
            "model": "llama-test",
            "max_tokens": 50,
            "messages": [
                {"role": "system", "content": "sys"},
                {"role": "user", "content": "hi"},
            ],
        }
    ]
