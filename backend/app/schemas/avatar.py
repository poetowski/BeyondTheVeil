import uuid

from pydantic import BaseModel

from app.models.avatar import AvatarTemplate


class AvatarTemplateOut(BaseModel):
    id: uuid.UUID
    slug: str
    name: str


def to_out(avatar: AvatarTemplate) -> AvatarTemplateOut:
    return AvatarTemplateOut(id=avatar.id, slug=avatar.slug, name=avatar.name)
