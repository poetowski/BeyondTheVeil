import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.item import EquipmentSlot, ItemInstance, ItemRarity


class ItemInstanceOut(BaseModel):
    id: uuid.UUID
    slug: str
    name: str
    slot: EquipmentSlot
    rarity: ItemRarity
    base_stats: dict[str, int]
    rolled_stats: dict[str, int] | None
    equipped_slot: EquipmentSlot | None
    damage_min: int | None
    damage_max: int | None
    spell_damage_min: int | None
    spell_damage_max: int | None
    defense: int
    bonus_max_hp: int
    rune_template_id: uuid.UUID | None
    rune_slug: str | None
    rune_name: str | None
    rune_stat_bonuses: dict[str, int] | None
    acquired_at: datetime


def to_out(item: ItemInstance) -> ItemInstanceOut:
    rune = item.rune_template
    return ItemInstanceOut(
        id=item.id,
        slug=item.template.slug,
        name=item.template.name,
        slot=item.template.slot,
        rarity=item.template.rarity,
        base_stats=item.template.base_stats,
        rolled_stats=item.rolled_stats,
        equipped_slot=item.equipped_slot,
        damage_min=item.template.damage_min,
        damage_max=item.template.damage_max,
        spell_damage_min=item.template.spell_damage_min,
        spell_damage_max=item.template.spell_damage_max,
        defense=item.template.defense,
        bonus_max_hp=item.template.bonus_max_hp,
        rune_template_id=rune.id if rune else None,
        rune_slug=rune.slug if rune else None,
        rune_name=rune.name if rune else None,
        rune_stat_bonuses=rune.stat_bonuses if rune else None,
        acquired_at=item.acquired_at,
    )
