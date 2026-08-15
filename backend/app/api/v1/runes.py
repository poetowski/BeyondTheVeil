from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.db import get_db
from app.models.user import User
from app.schemas.rune import RuneInstanceOut, to_out
from app.services import hero_service

router = APIRouter(prefix="/runes", tags=["runes"])


@router.get("", response_model=list[RuneInstanceOut])
def get_runes(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[RuneInstanceOut]:
    runes = hero_service.get_owned_runes(db, current_user.hero)
    return [to_out(rune) for rune in runes]
