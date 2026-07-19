from pydantic import BaseModel

from app.schemas.vehicle import VehicleSummary


class BrandRead(BaseModel):
    id: int
    name: str
    slug: str


class BrandList(BaseModel):
    items: list[BrandRead]


class TrimOverview(BaseModel):
    id: int
    name: str
    configurations: list[VehicleSummary]


class ModelOverview(BaseModel):
    brand: str
    model: str
    category: str | None
    trims: list[TrimOverview]
