import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.crafting import CraftingCategory
from app.models.material import MaterialInstance


class MaterialInstanceOut(BaseModel):
    id: uuid.UUID
    slug: str
    name: str
    description: str | None
    quantity: int
    category: CraftingCategory
    acquired_at: datetime


def to_out(material: MaterialInstance) -> MaterialInstanceOut:
    return MaterialInstanceOut(
        id=material.id,
        slug=material.template.slug,
        name=material.template.name,
        description=material.template.description,
        quantity=material.quantity,
        category=material.template.category,
        acquired_at=material.acquired_at,
    )
