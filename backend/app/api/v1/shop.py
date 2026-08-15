from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.db import get_db
from app.models.user import User
from app.schemas.shop import ShopBuyResultOut, ShopOut
from app.schemas.shop import buy_result_to_out, slot_to_out
from app.services import hero_service, shop_service

router = APIRouter(prefix="/shop", tags=["shop"])


@router.get("", response_model=ShopOut)
def get_shop(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> ShopOut:
    hero = current_user.hero
    today = shop_service.today_utc()
    slots = shop_service.roll_daily_shop(db, hero, today)
    purchased = shop_service.get_purchased_slot_indexes(db, hero, today)
    return ShopOut(shop_date=today, slots=[slot_to_out(s, s.slot_index in purchased) for s in slots])


@router.post("/buy/{slot_index}", response_model=ShopBuyResultOut)
def buy_shop_slot(
    slot_index: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> ShopBuyResultOut:
    try:
        result = shop_service.buy_shop_slot(db, current_user.hero, slot_index)
    except shop_service.InvalidSlotIndexError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except shop_service.SlotAlreadyPurchasedError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except hero_service.InsufficientGoldError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except shop_service.BackpackFullError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return buy_result_to_out(result)
