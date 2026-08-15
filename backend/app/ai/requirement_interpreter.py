"""Turns conversation text into StructuredRequirements, or a follow-up
question when the request is underspecified - see the
drivewise-ai-recommendations skill. This module only produces parameters;
it never filters or ranks the catalog itself.

NOTE: written without access to a live ANTHROPIC_API_KEY in this
environment, so it has not been exercised against the real API. Verify
against a real key before relying on it - in particular, whether Claude
reliably follows the JSON-only instruction, and whether the defensive
fallback below is ever actually hit in practice.
"""

import json
import re

import anthropic
from pydantic import BaseModel, ValidationError

from app.ai.client import get_client
from app.core.config import CLAUDE_MODEL
from app.schemas.conversation import ChatMessage
from app.schemas.requirement import StructuredRequirements

SYSTEM_PROMPT = """You are the requirement-extraction step of a car-buying assistant.
Read the conversation and the user's latest message, then respond with ONLY a JSON object,
no prose, no markdown code fences, matching this shape:

{
  "requirements": { <StructuredRequirements fields you are confident about, omit the rest> } | null,
  "follow_up_question": "<one focused question>" | null
}

StructuredRequirements fields: body_type (string), min_seats (int), budget_max (object with
amount and currency), fuel_type (string), drivetrain ("fwd" | "rwd" | "awd"),
priorities (list of short strings), notes (string).

Rules:
- Set exactly one of "requirements" or "follow_up_question", never both, never neither.
- Only set "requirements" once there is enough to search: at minimum a body type, a budget, or an
  explicit usage pattern (e.g. "family of 4", "city commuting").
- If the latest message refines a requirement already established earlier in the conversation
  (e.g. "actually make it cheaper"), merge it with what's already known rather than starting over.
- Never invent a value the user didn't state or clearly imply.
"""


class RequirementExtractionResult(BaseModel):
    requirements: StructuredRequirements | None = None
    follow_up_question: str | None = None


class RequirementInterpreter:
    """Wraps one Claude API call that turns free-text conversation into
    `StructuredRequirements`, per `drivewise-ai-recommendations`'s Code
    style section. Stateless beyond the injected client - safe to share a
    single instance across requests (see the module-level `interpreter`
    singleton at the bottom of this file).
    """

    def __init__(self, client: anthropic.Anthropic | None = None) -> None:
        """Args:
            client: Anthropic SDK client to use. Defaults to `None`, in
                which case `interpret` lazily resolves the shared client
                from `app.ai.client.get_client()` on first use - so
                constructing a `RequirementInterpreter` never fails just
                because `ANTHROPIC_API_KEY` isn't set; only calling
                `interpret` does. Pass an explicit client (e.g. a test
                double) to bypass that shared singleton.
        """
        self._client = client

    def _get_client(self) -> anthropic.Anthropic:
        """Returns the injected client, or lazily resolves the shared
        default on first use so constructing a `RequirementInterpreter`
        never fails just because `ANTHROPIC_API_KEY` isn't set yet (only
        calling `interpret` does).

        Returns:
            The Anthropic client this instance uses for API calls.
        """
        if self._client is None:
            self._client = get_client()
        return self._client

    @staticmethod
    def _strip_code_fences(text: str) -> str:
        """Removes a leading/trailing ```` ```json ... ``` ```` fence if
        the model added one despite the system prompt's "no markdown code
        fences" instruction.

        Args:
            text: Raw text content from the Claude API response.

        Returns:
            `text` with any surrounding code fence markers and outer
            whitespace stripped; unchanged if there was no fence.
        """
        text = text.strip()
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        return text.strip()

    def interpret(
        self, history: list[ChatMessage], latest_message: str
    ) -> RequirementExtractionResult:
        """Extracts structured requirements from a conversation turn, or
        produces a follow-up question when there isn't enough to search
        on yet.

        Defensive about the model not following the JSON-only
        instruction: strips stray code fences, validates against
        `RequirementExtractionResult`, and falls back to a generic
        follow-up question on any parse/validation failure rather than
        raising into the request path.

        Args:
            history: Prior turns of the conversation, oldest first. Does
                not include `latest_message`.
            latest_message: The user's newest message, extracted (and
                merged with prior turns) into requirements.

        Returns:
            A `RequirementExtractionResult` with exactly one of
            `requirements` or `follow_up_question` set - never both,
            never neither (enforced by the fallback branch even when the
            model's own output would have violated it).
        """
        client = self._get_client()

        transcript = "\n".join(f"{m.role}: {m.text}" for m in history)
        user_content = f"Conversation so far:\n{transcript}\n\nLatest message:\n{latest_message}"

        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_content}],
        )
        raw_text = "".join(block.text for block in response.content if block.type == "text")

        try:
            payload = json.loads(self._strip_code_fences(raw_text))
            return RequirementExtractionResult.model_validate(payload)
        except (json.JSONDecodeError, ValidationError):
            return RequirementExtractionResult(
                follow_up_question=(
                    "Could you tell me a bit more about how you'll use the car - who's riding "
                    "with you, where you mostly drive, and roughly what budget you have in mind?"
                )
            )


# Shared instance for callers that don't need a custom client (e.g. tests
# injecting a fake) - mirrors get_client()'s cached-singleton shape without
# needing its own cache, since construction here does no I/O.
interpreter = RequirementInterpreter()
