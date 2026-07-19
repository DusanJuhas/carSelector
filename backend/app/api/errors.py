from typing import Any, NoReturn

from fastapi import HTTPException


def api_error(status_code: int, code: str, message: str, details: dict[str, Any] | None = None) -> NoReturn:
    """Raises an HTTPException whose `detail` already matches the
    `ErrorResponse` shape from doc/api-contract.md, so the default FastAPI
    handler renders `{"detail": {"error": {...}}}`... except the contract
    wants `{"error": {...}}` at the top level, not nested under "detail" -
    see main.py's exception handler, which unwraps this.
    """
    raise HTTPException(
        status_code=status_code,
        detail={"error": {"code": code, "message": message, "details": details or {}}},
    )
