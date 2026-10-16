from fastapi import APIRouter

from app.schemas.health import HealthStatus

# Outside /api on purpose: it's for the hosting platform's probes (Render's
# healthCheckPath, see render.yaml), not part of the API contract in
# doc/api-contract.md.
router = APIRouter(tags=["health"])


@router.get("/healthz", response_model=HealthStatus)
def healthz() -> HealthStatus:
    """Liveness probe. Deliberately touches no database: the platform calls
    it every few seconds, and even a `SELECT 1` would keep a scale-to-zero
    Postgres (Neon Free suspends after 5 idle minutes) awake for as long as
    the web instance runs, using up its monthly compute allowance. A broken
    database connection shows up in the pages that need it instead.

    Returns:
        Always `{"status": "ok"}`.
    """
    return HealthStatus()
