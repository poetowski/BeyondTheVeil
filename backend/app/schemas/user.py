import uuid

from pydantic import BaseModel

from app.schemas.hero import HeroOut


class UserOut(BaseModel):
    id: uuid.UUID
    email: str


class UserMeResponse(BaseModel):
    user: UserOut
    hero: HeroOut
