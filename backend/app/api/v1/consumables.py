import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.db import get_db
from app.models.user import User
from app.schemas.consumable import ConsumableInstanceOut, to_out
from app.schemas.hero import HeroOut
from app.schemas.hero import to_out as hero_to_out
from app.schemas.shop import SellResultOut
from app.services import crafting_service, hero_service

router = APIRouter(prefix="/consumables", tags=["consumables"])


@router.get("", response_model=list[ConsumableInstanceOut])
def get_consumables(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[ConsumableInstanceOut]:
    consumables = hero_service.get_owned_consumables(db, current_user.hero)
    return [to_out(consumable) for consumable in consumables]


@router.post("/{consumable_id}/use", response_model=HeroOut)
def use_consumable(
    consumable_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> HeroOut:
    hero = current_user.hero
    try:
        crafting_service.use_consumable(db, hero, consumable_id)
    except crafting_service.ConsumableNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except crafting_service.ConsumableNotOwnedError as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc

    equipped_items = hero_service.get_equipped_items(db, hero)
    return hero_to_out(hero, equipped_items)


@router.post("/{consumable_id}/sell", response_model=SellResultOut)
def sell_consumable(
    consumable_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SellResultOut:
    try:
        gold_gained = hero_service.sell_consumable(db, current_user.hero, consumable_id)
    except hero_service.ConsumableNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except hero_service.ConsumableNotOwnedError as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    return SellResultOut(gold_gained=gold_gained)
