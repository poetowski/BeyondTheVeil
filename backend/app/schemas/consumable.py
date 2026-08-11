import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.consumable import ConsumableInstance


class ConsumableInstanceOut(BaseModel):
    id: uuid.UUID
    slug: str
    name: str
    description: str | None
    quantity: int
    acquired_at: datetime


def to_out(consumable: ConsumableInstance) -> ConsumableInstanceOut:
    return ConsumableInstanceOut(
        id=consumable.id,
        slug=consumable.template.slug,
        name=consumable.template.name,
        description=consumable.template.description,
        quantity=consumable.quantity,
        acquired_at=consumable.acquired_at,
    )
