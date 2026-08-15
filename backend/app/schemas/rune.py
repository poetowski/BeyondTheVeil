import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.rune import RuneInstance


class RuneInstanceOut(BaseModel):
    id: uuid.UUID
    slug: str
    name: str
    description: str | None
    stat_bonuses: dict[str, int]
    quantity: int
    acquired_at: datetime


def to_out(rune: RuneInstance) -> RuneInstanceOut:
    return RuneInstanceOut(
        id=rune.id,
        slug=rune.template.slug,
        name=rune.template.name,
        description=rune.template.description,
        stat_bonuses=rune.template.stat_bonuses,
        quantity=rune.quantity,
        acquired_at=rune.acquired_at,
    )
