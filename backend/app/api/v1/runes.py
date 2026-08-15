import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.db import get_db
from app.models.user import User
from app.schemas.rune import RuneInstanceOut, to_out
from app.schemas.shop import SellResultOut
from app.services import hero_service

router = APIRouter(prefix="/runes", tags=["runes"])


@router.get("", response_model=list[RuneInstanceOut])
def get_runes(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[RuneInstanceOut]:
    runes = hero_service.get_owned_runes(db, current_user.hero)
    return [to_out(rune) for rune in runes]


@router.post("/{rune_id}/sell", response_model=SellResultOut)
def sell_rune(
    rune_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SellResultOut:
    try:
        gold_gained = hero_service.sell_rune(db, current_user.hero, rune_id)
    except hero_service.RuneNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except hero_service.RuneNotOwnedError as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    return SellResultOut(gold_gained=gold_gained)
