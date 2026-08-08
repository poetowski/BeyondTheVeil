import uuid

from pydantic import BaseModel

from app.models.monster import MonsterTemplate


class MonsterTemplateOut(BaseModel):
    id: uuid.UUID
    slug: str
    name: str
    level_range_min: int
    level_range_max: int
    flavor_text: str | None


def to_out(monster: MonsterTemplate) -> MonsterTemplateOut:
    return MonsterTemplateOut(
        id=monster.id,
        slug=monster.slug,
        name=monster.name,
        level_range_min=monster.level_range_min,
        level_range_max=monster.level_range_max,
        flavor_text=monster.flavor_text,
    )
