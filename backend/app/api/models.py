from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.errors import api_error
from app.schemas.catalog import ModelOverview
from app.services import catalog

router = APIRouter(prefix="/models", tags=["models"])


@router.get("/{model_id}", response_model=ModelOverview)
def get_model_overview(model_id: int, db: Session = Depends(get_db)) -> ModelOverview:
    overview = catalog.get_model_overview(db, model_id)
    if overview is None:
        api_error(404, "model_not_found", f"No model with id {model_id}")
    return overview
