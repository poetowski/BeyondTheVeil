from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.db import get_db
from app.models.monster import MonsterTemplate
from app.models.user import User
from app.schemas.monster import MonsterTemplateOut, to_out

router = APIRouter(prefix="/bestiary", tags=["bestiary"])


@router.get("", response_model=list[MonsterTemplateOut])
def get_bestiary(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[MonsterTemplateOut]:
    monsters = (
        db.execute(
            select(MonsterTemplate).order_by(
                MonsterTemplate.level_range_min,
                MonsterTemplate.level_range_max,
                MonsterTemplate.name,
            )
        )
        .scalars()
        .all()
    )
    return [to_out(monster) for monster in monsters]
