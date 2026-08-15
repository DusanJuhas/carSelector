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


class RecommendationEngine:
    """Filters the catalog on hard constraints, then scores and ranks the
    rest, per `drivewise-ai-recommendations`'s Code style section.
    Stateless (the scoring weights are fixed class constants, not
    per-instance config yet) - a single shared instance is fine (see the
    module-level `engine` singleton at the bottom of this file).
    """

    # Drivetrain is treated as a soft preference here, not a hard filter:
    # the scripted example this product is built around ("AWD for
    # mountain trips" -> "AWD optional for city commuting") explicitly
    # downgrades it to a nice-to-have mid-conversation, so excluding
    # non-matching drivetrains outright would wrongly drop viable cars.
    # `catalog.list_vehicles` still accepts drivetrain as a hard filter
    # for direct catalog browsing/search, where an explicit user filter
    # should behave like one.
    DRIVETRAIN_MATCH_WEIGHT = 20.0
    PRIORITY_MATCH_WEIGHT = 10.0
    BUDGET_HEADROOM_WEIGHT = 20.0
    BASE_SCORE = 50.0

    def _score(self, vehicle: VehicleSummary, requirements: StructuredRequirements) -> float:
        """Computes a soft-preference match score for one already
        hard-filtered candidate vehicle.

        Args:
            vehicle: A candidate that already passed the hard filters
                (body_type, budget, fuel_type) in `catalog.list_vehicles`.
            requirements: The structured requirements to score against.

        Returns:
            A score starting at `BASE_SCORE`, increased for a matching
            drivetrain, each matched priority, and budget headroom (more
            headroom scores higher, capped by `BUDGET_HEADROOM_WEIGHT`).
            Not bounded to any fixed range beyond that.
        """
        score = self.BASE_SCORE

        if requirements.drivetrain is not None and requirements.drivetrain.value.upper() in vehicle.specs:
            score += self.DRIVETRAIN_MATCH_WEIGHT

        for priority in requirements.priorities:
            if any(priority.lower() in tag.lower() for tag in vehicle.specs):
                score += self.PRIORITY_MATCH_WEIGHT

        if requirements.budget_max is not None and vehicle.price.currency == requirements.budget_max.currency:
            # Reward comfortably-under-budget over barely-under-budget.
            headroom = (requirements.budget_max.amount - vehicle.price.amount) / requirements.budget_max.amount
            score += max(0.0, headroom) * self.BUDGET_HEADROOM_WEIGHT

        return score

    def recommend(
        self,
        db: Session,
        requirements: StructuredRequirements,
        *,
        market: str = catalog.DEFAULT_MARKET,
        limit: int = 10,
    ) -> list[VehicleSummary]:
        """Filters the catalog on hard constraints, then scores and ranks
        the rest.

        Hard constraints: body_type, budget, fuel_type (hard-filtered via
        `catalog.list_vehicles`). Soft preferences: drivetrain,
        priorities, budget headroom (scored by `_score`). `min_seats` is
        accepted on the contract's `StructuredRequirements` but has no
        backing data yet - see `catalog.list_vehicles`'s docstring - so
        it's a no-op here too.

        `flag` (e.g. "Over budget by ~2,200 Kc") from the design concept
        is intentionally not populated: that behavior means relaxing the
        budget filter and including some over-budget results anyway,
        which is a product decision this pass doesn't make. Budget stays
        a strict hard filter for now.

        Args:
            db: Database session to query the catalog through.
            requirements: Structured output of the AI requirement
                interpreter (or a direct caller building one manually).
            market: Market to price and filter against.
            limit: Maximum number of ranked results to return.

        Returns:
            Vehicles ranked best-first (highest score to lowest), each
            with `match_score` set to the rounded score capped at 100,
            and the top result (if any) flagged `top_pick=True`.
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
            ((self._score(vehicle, requirements), vehicle) for vehicle in candidates),
            key=lambda pair: pair[0],
            reverse=True,
        )[:limit]

        results = [
            vehicle.model_copy(update={"match_score": min(round(score), 100)}) for score, vehicle in scored
        ]
        if results:
            results[0] = results[0].model_copy(update={"top_pick": True})
        return results


# Shared instance for callers that don't need a custom configuration -
# construction here does no I/O, so a fresh instance would be just as
# cheap, but a shared one keeps the "one engine" mental model consistent
# with the AI-layer singletons in app/ai/.
engine = RecommendationEngine()
