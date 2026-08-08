import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.item import EquipmentSlot, ItemInstance, ItemRarity


class ItemInstanceOut(BaseModel):
    id: uuid.UUID
    name: str
    slot: EquipmentSlot
    rarity: ItemRarity
    base_stats: dict[str, int]
    rolled_stats: dict[str, int] | None
    equipped_slot: EquipmentSlot | None
    acquired_at: datetime


def to_out(item: ItemInstance) -> ItemInstanceOut:
    return ItemInstanceOut(
        id=item.id,
        name=item.template.name,
        slot=item.template.slot,
        rarity=item.template.rarity,
        base_stats=item.template.base_stats,
        rolled_stats=item.rolled_stats,
        equipped_slot=item.equipped_slot,
        acquired_at=item.acquired_at,
    )
