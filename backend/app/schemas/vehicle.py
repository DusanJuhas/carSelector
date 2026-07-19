from datetime import date

from pydantic import BaseModel

from app.models.enums import ColorFinish, ConsumptionUnit, Drivetrain, FuelType, OptionCategory
from app.schemas.common import Money


class PowertrainSpec(BaseModel):
    fuel_type: FuelType
    transmission: str | None
    drivetrain: Drivetrain
    power_kw: int | None
    power_hp: int | None
    consumption_min: float | None
    consumption_max: float | None
    consumption_unit: ConsumptionUnit | None
    co2_min_g_km: int | None
    co2_max_g_km: int | None


class ColorOption(BaseModel):
    name: str
    finish_type: ColorFinish | None
    surcharge: Money


class OptionLine(BaseModel):
    name: str
    category: OptionCategory
    surcharge: Money


class PricePoint(BaseModel):
    valid_from: date
    valid_to: date | None
    price: Money
    lowest_price_30d: Money | None


class VehicleSummary(BaseModel):
    """The recommendation-card / results-grid shape - one row per
    `configuration`, flattened for display. Corresponds to the frontend's
    `Car` type in `frontend/src/types/car.ts`, which still needs updating
    to match (notably: price becomes Money, not a formatted string).
    """

    configuration_id: int
    brand: str
    model: str
    trim: str
    price: Money
    match_score: int | None = None
    specs: list[str]
    flag: str | None = None
    top_pick: bool = False
    thumbnail_url: str | None = None
    # AI-generated, grounded only in this vehicle's own specs (see
    # app/ai/explanation_generator.py). Null outside a chat/recommendation
    # context, or if the AI layer isn't configured.
    explanation: str | None = None


class VehicleDetail(VehicleSummary):
    powertrain: PowertrainSpec
    colors: list[ColorOption]
    standard_equipment: list[str]
    optional_equipment: list[OptionLine]
    price_history: list[PricePoint]


class VehicleCompareResponse(BaseModel):
    vehicles: list[VehicleDetail]
