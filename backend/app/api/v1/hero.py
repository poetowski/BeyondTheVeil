from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.db import get_db
from app.models.user import User
from app.schemas.hero import HeroOut, StatTrainRequest
from app.schemas.hero import to_out as hero_to_out
from app.services import hero_service

router = APIRouter(prefix="/hero", tags=["hero"])


@router.post("/train", response_model=HeroOut)
def train_stat(
    body: StatTrainRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> HeroOut:
    hero = current_user.hero
    try:
        hero_service.train_stat(db, hero, body.stat)
    except hero_service.InsufficientGoldError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    equipped_items = hero_service.get_equipped_items(db, hero)
    return hero_to_out(hero, equipped_items)
