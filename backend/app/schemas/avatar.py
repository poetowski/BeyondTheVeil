import uuid

from pydantic import BaseModel

from app.models.avatar import AvatarTemplate


class AvatarTemplateOut(BaseModel):
    id: uuid.UUID
    slug: str
    name: str
    price: int
    level_requirement: int
    unlocked: bool


def to_out(avatar: AvatarTemplate, *, unlocked: bool) -> AvatarTemplateOut:
    return AvatarTemplateOut(
        id=avatar.id,
        slug=avatar.slug,
        name=avatar.name,
        price=avatar.price,
        level_requirement=avatar.level_requirement,
        unlocked=unlocked,
    )
