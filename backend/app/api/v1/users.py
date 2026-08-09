from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.db import get_db
from app.models.user import User
from app.schemas.hero import to_out as hero_to_out
from app.schemas.user import UserMeResponse, UserOut
from app.services import hero_service

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserMeResponse)
def get_me(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> UserMeResponse:
    hero = current_user.hero
    equipped_items = hero_service.get_equipped_items(db, hero)

    return UserMeResponse(
        user=UserOut(id=current_user.id, email=current_user.email),
        hero=hero_to_out(hero, equipped_items),
    )
