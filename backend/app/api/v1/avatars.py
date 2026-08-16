from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.db import get_db
from app.models.avatar import AvatarTemplate
from app.models.user import User
from app.schemas.avatar import AvatarTemplateOut, to_out
from app.schemas.hero import HeroOut
from app.schemas.hero import to_out as hero_to_out
from app.services import hero_service

router = APIRouter(prefix="/avatars", tags=["avatars"])


@router.get("", response_model=list[AvatarTemplateOut])
def get_avatars(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[AvatarTemplateOut]:
    avatars = (
        db.execute(select(AvatarTemplate).order_by(AvatarTemplate.sort_order, AvatarTemplate.name))
        .scalars()
        .all()
    )
    hero = current_user.hero
    return [
        to_out(avatar, unlocked=hero_service.is_avatar_unlocked(db, hero, avatar))
        for avatar in avatars
    ]


@router.post("/{avatar_slug}/unlock", response_model=HeroOut)
def unlock_avatar(
    avatar_slug: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> HeroOut:
    hero = current_user.hero
    try:
        hero_service.unlock_avatar(db, hero, avatar_slug)
    except hero_service.AvatarNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except hero_service.InsufficientGoldError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    equipped_items = hero_service.get_equipped_items(db, hero)
    return hero_to_out(hero, equipped_items)
