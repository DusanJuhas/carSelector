"""Shared Anthropic client factory. Every Claude API call in this codebase
goes through this module - see CLAUDE.md: "Pristup k Claude API pouze pres
/app/ai modul, nikde jinde v kodu."
"""

from functools import lru_cache

import anthropic

from app.core.config import ANTHROPIC_API_KEY


@lru_cache(maxsize=1)
def get_client() -> anthropic.Anthropic:
    if not ANTHROPIC_API_KEY:
        raise RuntimeError(
            "ANTHROPIC_API_KEY is not set. The AI layer (requirement "
            "extraction, explanations) cannot run without it - set it in "
            "the environment or backend/.env."
        )
    return anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
