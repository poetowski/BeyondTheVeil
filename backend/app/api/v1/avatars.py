from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.db import get_db
from app.models.avatar import AvatarTemplate
from app.models.user import User
from app.schemas.avatar import AvatarTemplateOut, to_out

router = APIRouter(prefix="/avatars", tags=["avatars"])


@router.get("", response_model=list[AvatarTemplateOut])
def get_avatars(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[AvatarTemplateOut]:
    avatars = db.execute(select(AvatarTemplate).order_by(AvatarTemplate.name)).scalars().all()
    return [to_out(avatar) for avatar in avatars]
