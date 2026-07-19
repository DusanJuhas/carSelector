from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class Money(BaseModel):
    amount: float
    currency: str


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: dict[str, Any] = {}


class ErrorResponse(BaseModel):
    error: ErrorDetail


class Page(BaseModel, Generic[T]):
    items: list[T]
    page: int
    page_size: int
    total: int
