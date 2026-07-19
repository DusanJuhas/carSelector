from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.catalog import BrandList
from app.services import catalog

router = APIRouter(prefix="/brands", tags=["brands"])


@router.get("", response_model=BrandList)
def list_brands(db: Session = Depends(get_db)) -> BrandList:
    return BrandList(items=catalog.list_brands(db))
