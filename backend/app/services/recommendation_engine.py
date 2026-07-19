"""Deterministic filter + rank over the catalog. No AI here - the AI layer
(`app/ai`) only produces `StructuredRequirements` and, afterwards, per-result
explanations; this module owns retrieval and ordering, per the
drivewise-ai-recommendations skill's guardrail: "the AI never reads or ranks
the database directly."
"""

from sqlalchemy.orm import Session

from app.models.enums import FuelType
from app.schemas.requirement import StructuredRequirements
from app.schemas.vehicle import VehicleSummary
from app.services import catalog

# Drivetrain is treated as a soft preference here, not a hard filter: the
# scripted example this product is built around ("AWD for mountain trips"
# -> "AWD optional for city commuting") explicitly downgrades it to a
# nice-to-have mid-conversation, so excluding non-matching drivetrains
# outright would wrongly drop viable cars. `catalog.list_vehicles` still
# accepts drivetrain as a hard filter for direct catalog browsing/search,
# where an explicit user filter should behave like one.
_DRIVETRAIN_MATCH_WEIGHT = 20.0
_PRIORITY_MATCH_WEIGHT = 10.0
_BUDGET_HEADROOM_WEIGHT = 20.0
_BASE_SCORE = 50.0


def _score(vehicle: VehicleSummary, requirements: StructuredRequirements) -> float:
    score = _BASE_SCORE

    if requirements.drivetrain is not None and requirements.drivetrain.value.upper() in vehicle.specs:
        score += _DRIVETRAIN_MATCH_WEIGHT

    for priority in requirements.priorities:
        if any(priority.lower() in tag.lower() for tag in vehicle.specs):
            score += _PRIORITY_MATCH_WEIGHT

    if requirements.budget_max is not None and vehicle.price.currency == requirements.budget_max.currency:
        # Reward comfortably-under-budget over barely-under-budget.
        headroom = (requirements.budget_max.amount - vehicle.price.amount) / requirements.budget_max.amount
        score += max(0.0, headroom) * _BUDGET_HEADROOM_WEIGHT

    return score


def recommend(
    db: Session,
    requirements: StructuredRequirements,
    *,
    market: str = catalog.DEFAULT_MARKET,
    limit: int = 10,
) -> list[VehicleSummary]:
    """Filter the catalog on hard constraints, then score + rank the rest.

    Hard constraints: body_type, budget, fuel_type (hard-filtered via
    `catalog.list_vehicles`). Soft preferences: drivetrain, priorities,
    budget headroom (scored below). `min_seats` is accepted on the
    contract's StructuredRequirements but has no backing data yet - see
    `catalog.list_vehicles`'s docstring - so it's a no-op here too.

    `flag` (e.g. "Over budget by ~2,200 Kc") from the design concept is
    intentionally not populated: that behavior means relaxing the budget
    filter and including some over-budget results anyway, which is a
    product decision this pass doesn't make. Budget stays a strict hard
    filter for now.
    """
    fuel_type = None
    if requirements.fuel_type:
        try:
            fuel_type = FuelType(requirements.fuel_type)
        except ValueError:
            fuel_type = None

    candidates = catalog.list_vehicles(
        db,
        body_type=requirements.body_type,
        fuel_type=fuel_type,
        budget_max=requirements.budget_max.amount if requirements.budget_max else None,
        currency=requirements.budget_max.currency if requirements.budget_max else "CZK",
        market=market,
        page=1,
        page_size=100,
    ).items

    scored = sorted(
        ((_score(vehicle, requirements), vehicle) for vehicle in candidates),
        key=lambda pair: pair[0],
        reverse=True,
    )[:limit]

    results = [
        vehicle.model_copy(update={"match_score": min(round(score), 100)}) for score, vehicle in scored
    ]
    if results:
        results[0] = results[0].model_copy(update={"top_pick": True})
    return results
