from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.errors import api_error
from app.models.enums import Drivetrain, FuelType
from app.schemas.common import Page
from app.schemas.vehicle import VehicleCompareResponse, VehicleDetail, VehicleSummary
from app.services import catalog

router = APIRouter(prefix="/vehicles", tags=["vehicles"])


@router.get("", response_model=Page[VehicleSummary])
def list_vehicles(
    body_type: str | None = None,
    budget_max: float | None = None,
    currency: str = "CZK",
    fuel_type: FuelType | None = None,
    drivetrain: Drivetrain | None = None,
    market: str = catalog.DEFAULT_MARKET,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> Page[VehicleSummary]:
    return catalog.list_vehicles(
        db,
        body_type=body_type,
        fuel_type=fuel_type,
        drivetrain=drivetrain,
        budget_max=budget_max,
        currency=currency,
        market=market,
        page=page,
        page_size=page_size,
    )


@router.get("/compare", response_model=VehicleCompareResponse)
def compare_vehicles(
    ids: str = Query(..., description="Comma-separated configuration ids, 2-4"),
    market: str = catalog.DEFAULT_MARKET,
    db: Session = Depends(get_db),
) -> VehicleCompareResponse:
    try:
        configuration_ids = [int(part) for part in ids.split(",") if part.strip()]
    except ValueError:
        api_error(400, "invalid_ids", "`ids` must be a comma-separated list of integers")

    if not 2 <= len(configuration_ids) <= 4:
        api_error(400, "invalid_id_count", "`ids` must contain between 2 and 4 configuration ids")

    found, missing = catalog.compare_vehicles(db, configuration_ids, market=market)
    if missing:
        api_error(
            404,
            "vehicle_not_found",
            f"Unknown configuration id(s): {missing}",
            {"missing_ids": missing},
        )
    return VehicleCompareResponse(vehicles=found)


@router.get("/{configuration_id}", response_model=VehicleDetail)
def get_vehicle(
    configuration_id: int,
    market: str = catalog.DEFAULT_MARKET,
    db: Session = Depends(get_db),
) -> VehicleDetail:
    detail = catalog.get_vehicle_detail(db, configuration_id, market=market)
    if detail is None:
        api_error(404, "vehicle_not_found", f"No vehicle with configuration id {configuration_id}")
    return detail
