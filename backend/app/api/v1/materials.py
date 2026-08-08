from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.db import get_db
from app.models.user import User
from app.schemas.material import MaterialInstanceOut, to_out
from app.services import hero_service

router = APIRouter(prefix="/materials", tags=["materials"])


@router.get("", response_model=list[MaterialInstanceOut])
def get_materials(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[MaterialInstanceOut]:
    materials = hero_service.get_owned_materials(db, current_user.hero)
    return [to_out(material) for material in materials]
