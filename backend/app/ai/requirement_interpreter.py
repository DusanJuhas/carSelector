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


def _strip_code_fences(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def extract_requirements(history: list[ChatMessage], latest_message: str) -> RequirementExtractionResult:
    """Defensive about the model not following the JSON-only instruction:
    strips stray code fences, validates against RequirementExtractionResult,
    and falls back to a generic follow-up question on any parse/validation
    failure rather than raising into the request path.
    """
    client = get_client()

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
        payload = json.loads(_strip_code_fences(raw_text))
        return RequirementExtractionResult.model_validate(payload)
    except (json.JSONDecodeError, ValidationError):
        return RequirementExtractionResult(
            follow_up_question=(
                "Could you tell me a bit more about how you'll use the car - who's riding "
                "with you, where you mostly drive, and roughly what budget you have in mind?"
            )
        )
