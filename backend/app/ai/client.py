"""Shared Anthropic client factory. Every Claude API call in this codebase
goes through this module - see CLAUDE.md: "Pristup k Claude API pouze pres
/app/ai modul, nikde jinde v kodu."
"""

from functools import lru_cache

import anthropic

from app.core.config import ANTHROPIC_API_KEY


@lru_cache(maxsize=1)
def get_client() -> anthropic.Anthropic:
    """Returns the shared Anthropic client, creating it on first call.

    A plain cached factory function rather than a class: there's no
    per-instance state or behavior beyond "build once, reuse" - `
    lru_cache(maxsize=1)` already gives that, so a class would only add
    ceremony (see `drivewise-architecture`'s Code style section on when
    a class is/isn't worth it). `RequirementInterpreter` and
    `ExplanationGenerator` each accept a client via dependency injection
    and call this as their default.

    Returns:
        A process-wide singleton `anthropic.Anthropic` client, authenticated
        with `ANTHROPIC_API_KEY`.

    Raises:
        RuntimeError: `ANTHROPIC_API_KEY` isn't set. Raised here (at
            first use) rather than at import time, so the rest of the
            app - the catalog endpoints in particular - still works
            without it.
    """
    if not ANTHROPIC_API_KEY:
        raise RuntimeError(
            "ANTHROPIC_API_KEY is not set. The AI layer (requirement "
            "extraction, explanations) cannot run without it - set it in "
            "the environment or backend/.env."
        )
    return anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
