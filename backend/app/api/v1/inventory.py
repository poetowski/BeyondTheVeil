import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.db import get_db
from app.models.user import User
from app.schemas.item import ItemInstanceOut, to_out
from app.schemas.shop import SellResultOut
from app.services import hero_service

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.get("", response_model=list[ItemInstanceOut])
def get_inventory(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[ItemInstanceOut]:
    items = hero_service.get_owned_items(db, current_user.hero)
    return [to_out(item) for item in items]


@router.post("/{item_id}/equip", response_model=ItemInstanceOut)
def equip_item(
    item_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ItemInstanceOut:
    try:
        item = hero_service.equip_item(db, current_user.hero, item_id)
    except hero_service.ItemNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except hero_service.ItemNotOwnedError as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except hero_service.LevelRequirementNotMetError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return to_out(item)


@router.post("/{item_id}/unequip", response_model=ItemInstanceOut)
def unequip_item(
    item_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ItemInstanceOut:
    try:
        item = hero_service.unequip_item(db, current_user.hero, item_id)
    except hero_service.ItemNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except hero_service.ItemNotOwnedError as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    return to_out(item)


@router.post("/{item_id}/apply-rune/{rune_instance_id}", response_model=ItemInstanceOut)
def apply_rune(
    item_id: uuid.UUID,
    rune_instance_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ItemInstanceOut:
    try:
        item = hero_service.apply_rune(db, current_user.hero, item_id, rune_instance_id)
    except (hero_service.ItemNotFoundError, hero_service.RuneNotFoundError) as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except (hero_service.ItemNotOwnedError, hero_service.RuneNotOwnedError) as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except hero_service.RuneAlreadyAppliedError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return to_out(item)


@router.post("/{item_id}/sell", response_model=SellResultOut)
def sell_item(
    item_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SellResultOut:
    try:
        gold_gained = hero_service.sell_item(db, current_user.hero, item_id)
    except hero_service.ItemNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except hero_service.ItemNotOwnedError as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except hero_service.ItemEquippedError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return SellResultOut(gold_gained=gold_gained)
