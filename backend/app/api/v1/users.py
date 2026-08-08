from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.db import get_db
from app.models.user import User
from app.schemas.hero import HeroOut
from app.schemas.user import UserMeResponse, UserOut
from app.services import hero_service

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserMeResponse)
def get_me(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> UserMeResponse:
    hero = current_user.hero
    equipped_items = hero_service.get_equipped_items(db, hero)
    base = hero_service.compute_base_stats(hero)
    bonus = hero_service.compute_stat_bonuses(hero, equipped_items)
    effective = {stat: base[stat] + bonus[stat] for stat in hero_service.STAT_NAMES}
    max_hp = hero_service.compute_max_hp(effective["vitality"])

    return UserMeResponse(
        user=UserOut(id=current_user.id, email=current_user.email),
        hero=HeroOut(
            id=hero.id,
            name=hero.name,
            level=hero.level,
            xp=hero.xp,
            max_hp=max_hp,
            **effective,
            **{f"base_{stat}": value for stat, value in base.items()},
            **{f"bonus_{stat}": value for stat, value in bonus.items()},
        ),
    )
