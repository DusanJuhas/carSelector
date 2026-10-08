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


class TrimChoice(BaseModel):
    """One trim of a model, represented by a single configuration - see
    `catalog.list_trim_alternatives`."""

    trim_id: int
    trim_name: str
    vehicle: VehicleSummary
    # The configuration has the same powertrain as the one asked about, so
    # comparing it isolates the equipment differences.
    same_engine: bool
    is_current: bool


class ModelOverview(BaseModel):
    brand: str
    model: str
    category: str | None
    trims: list[TrimOverview]
