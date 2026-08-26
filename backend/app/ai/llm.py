"""Provider-agnostic LLM interface. `RequirementInterpreter` and
`ExplanationGenerator` call `LlmClient.complete()` without knowing whether
the actual API underneath is Anthropic or Groq - see `app/ai/client.py`
for provider selection (`AI_PROVIDER`).
"""

from typing import Protocol

import anthropic
import groq


class LlmClient(Protocol):
    """One system-prompted, single-turn text completion call - the only
    shape `app/ai/requirement_interpreter.py` and
    `app/ai/explanation_generator.py` need from an LLM provider.
    """

    def complete(self, *, system: str, user_content: str, max_tokens: int) -> str:
        """Sends one system+user turn and returns the model's reply text.

        Args:
            system: System prompt.
            user_content: The user-turn content (already fully composed -
                callers build the whole prompt string themselves).
            max_tokens: Upper bound on the reply length.

        Returns:
            The model's text reply, concatenated if the provider returns
            it in multiple parts.
        """
        ...


class AnthropicLlmClient:
    """`LlmClient` backed by the Anthropic Messages API."""

    def __init__(self, client: anthropic.Anthropic, model: str) -> None:
        """Args:
            client: An authenticated Anthropic SDK client.
            model: Model id to pass as `model=` on every call, e.g.
                `CLAUDE_MODEL`.
        """
        self._client = client
        self._model = model

    def complete(self, *, system: str, user_content: str, max_tokens: int) -> str:
        """See `LlmClient.complete`."""
        response = self._client.messages.create(
            model=self._model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user_content}],
        )
        return "".join(block.text for block in response.content if block.type == "text")


class GroqLlmClient:
    """`LlmClient` backed by Groq's OpenAI-compatible chat completions API."""

    def __init__(self, client: groq.Groq, model: str) -> None:
        """Args:
            client: An authenticated Groq SDK client.
            model: Model id to pass as `model=` on every call, e.g.
                `GROQ_MODEL`.
        """
        self._client = client
        self._model = model

    def complete(self, *, system: str, user_content: str, max_tokens: int) -> str:
        """See `LlmClient.complete`. Groq has no separate `system=`
        parameter (unlike Anthropic) - the system prompt is just the
        first message, with role `"system"`.
        """
        response = self._client.chat.completions.create(
            model=self._model,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_content},
            ],
        )
        return response.choices[0].message.content or ""
