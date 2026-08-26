"""Shared LLM client factory. Every AI-provider API call in this codebase
goes through this module - see CLAUDE.md: "Pristup k Claude API pouze pres
/app/ai modul, nikde jinde v kodu." (the same rule now covers Groq too,
the other supported provider - see `AI_PROVIDER`).
"""

from functools import lru_cache

import anthropic
import groq

from app.ai.llm import AnthropicLlmClient, GroqLlmClient, LlmClient
from app.core.config import (
    AI_PROVIDER,
    ANTHROPIC_API_KEY,
    CLAUDE_MODEL,
    GROQ_API_KEY,
    GROQ_MODEL,
)


@lru_cache(maxsize=1)
def get_client() -> LlmClient:
    """Returns the shared LLM client for whichever provider `AI_PROVIDER`
    selects, creating it on first call.

    A plain cached factory function rather than a class: there's no
    per-instance state or behavior beyond "build once, reuse" - `
    lru_cache(maxsize=1)` already gives that, so a class would only add
    ceremony (see `drivewise-architecture`'s Code style section on when
    a class is/isn't worth it). `RequirementInterpreter` and
    `ExplanationGenerator` each accept a client via dependency injection
    and call this as their default.

    Returns:
        A process-wide singleton `LlmClient` (`AnthropicLlmClient` or
        `GroqLlmClient`, per `AI_PROVIDER`), authenticated with the
        selected provider's API key.

    Raises:
        RuntimeError: `AI_PROVIDER` isn't a recognized value, or the
            selected provider's API key isn't set. Raised here (at first
            use) rather than at import time, so the rest of the app - the
            catalog endpoints in particular - still works without it.
    """
    if AI_PROVIDER == "groq":
        if not GROQ_API_KEY:
            raise RuntimeError(
                "AI_PROVIDER is 'groq' but GROQ_API_KEY is not set. The AI layer (requirement "
                "extraction, explanations) cannot run without it - set it in the environment or "
                "backend/.env, or switch AI_PROVIDER back to 'anthropic'."
            )
        return GroqLlmClient(groq.Groq(api_key=GROQ_API_KEY), GROQ_MODEL)

    if AI_PROVIDER != "anthropic":
        raise RuntimeError(
            f"Unknown AI_PROVIDER {AI_PROVIDER!r} - expected 'anthropic' or 'groq'."
        )
    if not ANTHROPIC_API_KEY:
        raise RuntimeError(
            "ANTHROPIC_API_KEY is not set. The AI layer (requirement "
            "extraction, explanations) cannot run without it - set it in "
            "the environment or backend/.env, or set AI_PROVIDER=groq with a GROQ_API_KEY instead."
        )
    return AnthropicLlmClient(anthropic.Anthropic(api_key=ANTHROPIC_API_KEY), CLAUDE_MODEL)
