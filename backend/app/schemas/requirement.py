from pydantic import BaseModel, Field, field_validator

from app.models.enums import Drivetrain
from app.schemas.common import Money

# Currency spellings the LLM has been seen to (or plausibly could) emit in
# place of the ISO 4217 code the catalog's `prices.currency` stores. The
# catalog compares currencies by exact match, so a single "Kc" here used to
# filter out every car (reported: "SUV, 1,150,000 Kc, AWD" found nothing).
# Keys are lowercased and stripped of dots/whitespace before lookup.
_CURRENCY_ALIASES = {
    "kč": "CZK",
    "kc": "CZK",
    "czk": "CZK",
    "korun": "CZK",
    "koruna": "CZK",
    "koruny": "CZK",
    "€": "EUR",
    "eur": "EUR",
    "euro": "EUR",
    "eura": "EUR",
}


def normalize_currency(currency: str) -> str:
    """Maps a free-form currency spelling to its ISO 4217 code.

    Args:
        currency: Currency as produced by the AI layer, e.g. `"Kc"`,
            `"Kč"`, `"czk"` or already `"CZK"`.

    Returns:
        The ISO code for a known alias, otherwise the input stripped and
        uppercased (so an already-correct code passes through unchanged).
    """
    key = currency.strip().lower().replace(".", "").replace(" ", "")
    return _CURRENCY_ALIASES.get(key, currency.strip().upper())


class StructuredRequirements(BaseModel):
    """Output of the AI requirement-extraction step; input to the
    recommendation engine's filter/rank step. The AI never ranks or reads
    the database directly - it only produces this.
    """

    body_type: str | None = None
    min_seats: int | None = None
    budget_max: Money | None = None
    fuel_type: str | None = None
    drivetrain: Drivetrain | None = None
    priorities: list[str] = Field(default_factory=list)
    notes: str | None = None

    @field_validator("budget_max")
    @classmethod
    def _normalize_budget_currency(cls, value: Money | None) -> Money | None:
        """Normalizes the budget's currency to an ISO code - see
        `_CURRENCY_ALIASES`."""
        if value is None:
            return None
        return value.model_copy(update={"currency": normalize_currency(value.currency)})


class UserRequirement(BaseModel):
    """The human-readable "requirements drawer" card. Matches
    `frontend/src/types/requirement.ts` as-is. One of these is produced
    per populated field in StructuredRequirements by the backend, not the
    AI and not the frontend.
    """

    label: str
    value: str
    source: str
    changed: bool
