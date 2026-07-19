from pydantic import BaseModel, Field

from app.models.enums import Drivetrain
from app.schemas.common import Money


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
