from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.db import get_db
from app.models.user import User
from app.schemas import hero as hero_schema
from app.schemas.user import UserMeResponse, UserOut

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserMeResponse)
def get_me(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> UserMeResponse:
    return UserMeResponse(
        user=UserOut(id=current_user.id, email=current_user.email),
        hero=hero_schema.to_out(db, current_user.hero),
    )
