import hashlib
import random
import uuid
from dataclasses import dataclass
from datetime import date, datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.hero import Hero
from app.models.item import ItemInstance, ItemTemplate
from app.models.material import MaterialInstance, MaterialTemplate
from app.models.shop import ShopPurchase
from app.services import hero_service

GEAR_SLOT_COUNT = 4
MATERIAL_SLOT_COUNT = 2
TOTAL_SLOT_COUNT = GEAR_SLOT_COUNT + MATERIAL_SLOT_COUNT


class ShopServiceError(Exception):
    """Base class for shop roll/buy failures."""


class InvalidSlotIndexError(ShopServiceError):
    pass


class SlotAlreadyPurchasedError(ShopServiceError):
    pass


class BackpackFullError(ShopServiceError):
    pass


@dataclass
class ShopSlot:
    slot_index: int
    slot_type: str  # "item" | "material"
    template: ItemTemplate | MaterialTemplate


@dataclass
class BuyResult:
    slot_type: str
    item: ItemInstance | None
    material: MaterialInstance | None
    gold_spent: int


def today_utc() -> date:
    """UTC calendar date - deployment-independent, avoids local/server
    timezone ambiguity for "what day is it" (see _shop_seed)."""
    return datetime.now(timezone.utc).date()


def _shop_seed(hero_id: uuid.UUID, shop_date: date) -> int:
    """Deterministic per-(hero, date) seed: refetching /shop the same day
    always recomputes the same 6 slots without persisting anything. Uses a
    dedicated random.Random(seed) instance, same spirit as
    combat/encounter.py's independent RNG for monster selection - never
    shared with any other RNG use."""
    material = f"{hero_id}:{shop_date.isoformat()}"
    digest = hashlib.sha256(material.encode()).hexdigest()
    return int(digest, 16) % (2**63)


def roll_daily_shop(db: Session, hero: Hero, shop_date: date | None = None) -> list[ShopSlot]:
    shop_date = shop_date or today_utc()
    rng = random.Random(_shop_seed(hero.id, shop_date))

    # Ordered by slug (not raw DB row order) before sampling, so the roll is
    # reproducible regardless of physical row order - same reasoning as
    # encounter.py ordering MonsterTemplate by slug before rng.choice.
    item_templates = db.execute(select(ItemTemplate).order_by(ItemTemplate.slug)).scalars().all()
    material_templates = db.execute(select(MaterialTemplate).order_by(MaterialTemplate.slug)).scalars().all()

    gear_pick = rng.sample(item_templates, k=min(GEAR_SLOT_COUNT, len(item_templates)))
    material_pick = rng.sample(material_templates, k=min(MATERIAL_SLOT_COUNT, len(material_templates)))

    slots = [ShopSlot(slot_index=i, slot_type="item", template=t) for i, t in enumerate(gear_pick)]
    slots += [
        ShopSlot(slot_index=GEAR_SLOT_COUNT + i, slot_type="material", template=t)
        for i, t in enumerate(material_pick)
    ]
    return slots


def get_purchased_slot_indexes(db: Session, hero: Hero, shop_date: date | None = None) -> set[int]:
    shop_date = shop_date or today_utc()
    rows = (
        db.execute(
            select(ShopPurchase.slot_index).where(
                ShopPurchase.hero_id == hero.id, ShopPurchase.shop_date == shop_date
            )
        )
        .scalars()
        .all()
    )
    return set(rows)


def buy_shop_slot(db: Session, hero: Hero, slot_index: int, shop_date: date | None = None) -> BuyResult:
    """Verify-then-mutate, mirrors crafting_service.craft's two-pass shape:
    check not-already-bought, gold, and (gear only - materials aren't
    capacity-limited, see hero_service.get_backpack_used_capacity) backpack
    capacity before touching anything."""
    shop_date = shop_date or today_utc()
    slots = roll_daily_shop(db, hero, shop_date)
    slot = next((s for s in slots if s.slot_index == slot_index), None)
    if slot is None:
        raise InvalidSlotIndexError(f"slot {slot_index} does not exist")

    already = db.execute(
        select(ShopPurchase).where(
            ShopPurchase.hero_id == hero.id,
            ShopPurchase.shop_date == shop_date,
            ShopPurchase.slot_index == slot_index,
        )
    ).scalar_one_or_none()
    if already is not None:
        raise SlotAlreadyPurchasedError("this slot has already been bought today")

    price = slot.template.price
    if hero.gold < price:
        raise hero_service.InsufficientGoldError("not enough gold to buy this")

    if slot.slot_type == "item":
        used = hero_service.get_backpack_used_capacity(db, hero)
        if used + 1 > hero.inventory_capacity:
            raise BackpackFullError("not enough backpack space to hold this")

    hero.gold -= price
    db.add(hero)

    purchase = ShopPurchase(hero_id=hero.id, shop_date=shop_date, slot_index=slot_index, price_paid=price)

    item_result: ItemInstance | None = None
    material_result: MaterialInstance | None = None
    if slot.slot_type == "item":
        item_result = ItemInstance(template_id=slot.template.id, owner_hero_id=hero.id, equipped_slot=None)
        db.add(item_result)
        purchase.item_template_id = slot.template.id
    else:
        existing_stack = (
            db.execute(
                select(MaterialInstance).where(
                    MaterialInstance.owner_hero_id == hero.id,
                    MaterialInstance.template_id == slot.template.id,
                )
            )
            .scalars()
            .first()
        )
        if existing_stack is not None:
            existing_stack.quantity += 1
            db.add(existing_stack)
            material_result = existing_stack
        else:
            material_result = MaterialInstance(template_id=slot.template.id, owner_hero_id=hero.id, quantity=1)
            db.add(material_result)
        purchase.material_template_id = slot.template.id

    db.add(purchase)
    try:
        db.commit()
    except IntegrityError:
        # The unique (hero_id, shop_date, slot_index) constraint is the real
        # guarantee under a double-submit; the pre-check above just avoids
        # wasted work in the common case (same pattern as
        # veil_service._start_run's equipped-slot handling).
        db.rollback()
        raise SlotAlreadyPurchasedError("this slot has already been bought today") from None

    db.refresh(hero)
    if item_result is not None:
        db.refresh(item_result)
    if material_result is not None:
        db.refresh(material_result)

    return BuyResult(slot_type=slot.slot_type, item=item_result, material=material_result, gold_spent=price)
