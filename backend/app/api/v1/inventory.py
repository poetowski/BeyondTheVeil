from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.db import get_db
from app.models.user import User
from app.schemas.item import ItemInstanceOut, to_out
from app.services import hero_service

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.get("", response_model=list[ItemInstanceOut])
def get_inventory(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[ItemInstanceOut]:
    items = hero_service.get_owned_items(db, current_user.hero)
    return [to_out(item) for item in items]
