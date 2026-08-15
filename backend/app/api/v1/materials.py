import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.db import get_db
from app.models.user import User
from app.schemas.material import MaterialInstanceOut, to_out
from app.schemas.shop import SellResultOut
from app.services import hero_service

router = APIRouter(prefix="/materials", tags=["materials"])


@router.get("", response_model=list[MaterialInstanceOut])
def get_materials(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[MaterialInstanceOut]:
    materials = hero_service.get_owned_materials(db, current_user.hero)
    return [to_out(material) for material in materials]


@router.post("/{material_id}/sell", response_model=SellResultOut)
def sell_material(
    material_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SellResultOut:
    try:
        gold_gained = hero_service.sell_material(db, current_user.hero, material_id)
    except hero_service.MaterialNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except hero_service.MaterialNotOwnedError as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    return SellResultOut(gold_gained=gold_gained)
