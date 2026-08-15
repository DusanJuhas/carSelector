from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import brands, conversations, models, vehicles
from app.core.config import CORS_ALLOWED_ORIGINS

app = FastAPI(title="DriveWise AI API")

# The frontend (Vite dev server, a different origin/port) calls this API
# directly from the browser - no auth/cookies in v1 (see doc/api-contract.md),
# so a small fixed allowlist is enough; no credentials are sent.
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """doc/api-contract.md's error shape is `{"error": {...}}` at the top
    level - FastAPI's default wraps HTTPException.detail under `"detail"`
    instead, so unwrap it here. `app.api.errors.api_error` always sets
    `detail` to the contract shape already; anything else (FastAPI's own
    validation errors, etc.) gets wrapped generically.
    """
    if isinstance(exc.detail, dict) and "error" in exc.detail:
        return JSONResponse(status_code=exc.status_code, content=exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": "http_error", "message": str(exc.detail), "details": {}}},
    )


app.include_router(brands.router, prefix="/api")
app.include_router(models.router, prefix="/api")
app.include_router(vehicles.router, prefix="/api")
app.include_router(conversations.router, prefix="/api")
