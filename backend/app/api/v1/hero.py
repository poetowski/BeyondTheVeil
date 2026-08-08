from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.db import get_db
from app.models.user import User
from app.schemas import hero as hero_schema
from app.schemas.hero import AllocateStatRequest, HeroOut
from app.services import hero_service

router = APIRouter(prefix="/hero", tags=["hero"])


@router.post("/allocate-stat", response_model=HeroOut)
def allocate_stat(
    payload: AllocateStatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> HeroOut:
    hero = current_user.hero
    try:
        hero_service.allocate_stat_point(hero, payload.stat, payload.amount)
    except hero_service.InsufficientStatPointsError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except hero_service.InvalidStatError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    db.add(hero)
    db.commit()
    db.refresh(hero)
    return hero_schema.to_out(db, hero)
