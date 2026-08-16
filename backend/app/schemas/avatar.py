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
    # Non-null only for a price=0 avatar gated behind a specific in-game
    # action rather than reaching level_requirement alone (see
    # AvatarTemplate's docstring) - display copy for the locked card,
    # e.g. "Craft a Herbalist Hell potion in Alchemy (level 15) and drink
    # it" instead of the usual "Reach level X".
    unlock_hint: str | None


def to_out(avatar: AvatarTemplate, *, unlocked: bool) -> AvatarTemplateOut:
    return AvatarTemplateOut(
        id=avatar.id,
        slug=avatar.slug,
        name=avatar.name,
        price=avatar.price,
        level_requirement=avatar.level_requirement,
        unlocked=unlocked,
        unlock_hint=avatar.unlock_hint,
    )
