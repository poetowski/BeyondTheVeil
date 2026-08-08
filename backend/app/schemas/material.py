import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.material import MaterialInstance


class MaterialInstanceOut(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    quantity: int
    acquired_at: datetime


def to_out(material: MaterialInstance) -> MaterialInstanceOut:
    return MaterialInstanceOut(
        id=material.id,
        name=material.template.name,
        description=material.template.description,
        quantity=material.quantity,
        acquired_at=material.acquired_at,
    )
