import uuid
from datetime import date
from typing import Literal

from pydantic import BaseModel

from app.models.crafting import CraftingCategory
from app.models.item import EquipmentSlot, ItemRarity
from app.schemas.item import ItemInstanceOut
from app.schemas.item import to_out as item_to_out
from app.schemas.material import MaterialInstanceOut
from app.schemas.material import to_out as material_to_out
from app.services.shop_service import BuyResult, ShopSlot


class ShopSlotOut(BaseModel):
    slot_index: int
    slot_type: Literal["item", "material"]
    template_id: uuid.UUID
    slug: str
    name: str
    description: str | None
    price: int
    already_bought: bool
    item_slot: EquipmentSlot | None = None
    item_rarity: ItemRarity | None = None
    material_category: CraftingCategory | None = None


class ShopOut(BaseModel):
    shop_date: date
    slots: list[ShopSlotOut]


class ShopBuyResultOut(BaseModel):
    slot_type: Literal["item", "material"]
    item: ItemInstanceOut | None
    material: MaterialInstanceOut | None
    gold_spent: int


class SellResultOut(BaseModel):
    """Reused by every sell endpoint (inventory/materials/consumables/runes),
    despite living here - cross-file schema reuse is already normal in this
    codebase (e.g. consumables.py imports HeroOut from schemas/hero.py)."""

    gold_gained: int


def slot_to_out(slot: ShopSlot, already_bought: bool) -> ShopSlotOut:
    t = slot.template
    return ShopSlotOut(
        slot_index=slot.slot_index,
        slot_type=slot.slot_type,
        template_id=t.id,
        slug=t.slug,
        name=t.name,
        description=t.description,
        price=t.price,
        already_bought=already_bought,
        item_slot=t.slot if slot.slot_type == "item" else None,
        item_rarity=t.rarity if slot.slot_type == "item" else None,
        material_category=t.category if slot.slot_type == "material" else None,
    )


def buy_result_to_out(result: BuyResult) -> ShopBuyResultOut:
    return ShopBuyResultOut(
        slot_type=result.slot_type,
        item=item_to_out(result.item) if result.item is not None else None,
        material=material_to_out(result.material) if result.material is not None else None,
        gold_spent=result.gold_spent,
    )
