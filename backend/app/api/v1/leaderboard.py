from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.db import get_db
from app.models.user import User
from app.schemas.leaderboard import LeaderboardEntryOut, to_out
from app.services import hero_service

router = APIRouter(prefix="/leaderboard", tags=["leaderboard"])


@router.get("", response_model=list[LeaderboardEntryOut])
def get_leaderboard(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[LeaderboardEntryOut]:
    heroes = hero_service.get_leaderboard(db)
    return [to_out(rank, hero) for rank, hero in enumerate(heroes, start=1)]
