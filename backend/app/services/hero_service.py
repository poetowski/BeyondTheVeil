import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.hero import Hero
from app.models.item import ItemInstance
from app.models.material import MaterialInstance

STAT_NAMES = ("strength", "dexterity", "intelligence", "vitality", "agility", "spirit")

HP_PER_VITALITY = 10
BASE_HP = 50
BASELINE_STAT_VALUE = 10

# Placeholder curve/costs — balance pass pending, same spirit as the combat
# engine's placeholder constants.
XP_CURVE_BASE = 100
XP_CURVE_EXPONENT = 1.5
TRAIN_STAT_BASE_COST = 10


class HeroServiceError(Exception):
    """Base class for hero-mutation failures (equip, unequip, stat training)."""


class ItemNotFoundError(HeroServiceError):
    pass


class ItemNotOwnedError(HeroServiceError):
    pass


class LevelRequirementNotMetError(HeroServiceError):
    pass


class UnknownStatError(HeroServiceError):
    pass


class InsufficientGoldError(HeroServiceError):
    pass


def compute_base_stats(hero: Hero) -> dict[str, int]:
    return {stat: getattr(hero, stat) for stat in STAT_NAMES}


def compute_stat_bonuses(hero: Hero, equipped_items: list[ItemInstance]) -> dict[str, int]:
    """Bonuses from every currently-equipped item (weapon, armor, spell skill, etc.),
    isolated from base stats so base + bonus == effective by construction."""
    bonuses = {stat: 0 for stat in STAT_NAMES}
    for item in equipped_items:
        if item.equipped_slot is None:
            continue
        for source in (item.template.base_stats, item.rolled_stats):
            if not source:
                continue
            for stat, bonus in source.items():
                if stat in bonuses:
                    bonuses[stat] += bonus
    return bonuses


def compute_effective_stats(hero: Hero, equipped_items: list[ItemInstance]) -> dict[str, int]:
    """Base hero stats plus bonuses from every currently-equipped item."""
    base = compute_base_stats(hero)
    bonuses = compute_stat_bonuses(hero, equipped_items)
    return {stat: base[stat] + bonuses[stat] for stat in STAT_NAMES}


def compute_max_hp(effective_vitality: int) -> int:
    """Placeholder formula; combat balance is a separate future task."""
    return BASE_HP + effective_vitality * HP_PER_VITALITY


def xp_required_for_level(level: int) -> int:
    """XP needed to advance from `level` to `level + 1`."""
    return round(level**XP_CURVE_EXPONENT * XP_CURVE_BASE)


def apply_xp(hero: Hero, xp_gained: int) -> int:
    """Adds XP to the hero, leveling up (possibly multiple times) whenever the
    threshold for the hero's current level is reached. xp is a rolling
    progress-to-next-level counter, not lifetime total: it resets to the
    leftover remainder on every level-up. Level is purely a content gate here
    — it does not itself change any stat. Returns the number of levels gained.
    """
    hero.xp += xp_gained
    levels_gained = 0
    while hero.xp >= xp_required_for_level(hero.level):
        hero.xp -= xp_required_for_level(hero.level)
        hero.level += 1
        levels_gained += 1
    return levels_gained


def train_stat_cost(current_value: int) -> int:
    """Gold cost to raise a stat by one point from its current value. Costs
    scale up the further a stat has already been trained above baseline."""
    return TRAIN_STAT_BASE_COST * max(1, current_value - BASELINE_STAT_VALUE + 1)


def train_stat(db: Session, hero: Hero, stat: str) -> Hero:
    if stat not in STAT_NAMES:
        raise UnknownStatError(f"unknown stat: {stat}")

    cost = train_stat_cost(getattr(hero, stat))
    if hero.gold < cost:
        raise InsufficientGoldError("not enough gold to train this stat")

    hero.gold -= cost
    setattr(hero, stat, getattr(hero, stat) + 1)
    db.add(hero)
    db.commit()
    db.refresh(hero)
    return hero


def equip_item(db: Session, hero: Hero, item_id: uuid.UUID) -> ItemInstance:
    """Equips an owned item, auto-unequipping whatever currently occupies its
    slot (a single action swaps gear rather than requiring an explicit
    unequip first). The DB's partial unique index on (owner_hero_id,
    equipped_slot) remains the actual invariant guarantee; this just keeps a
    normal equip from tripping over it."""
    item = db.get(ItemInstance, item_id)
    if item is None:
        raise ItemNotFoundError(f"item {item_id} not found")
    if item.owner_hero_id != hero.id:
        raise ItemNotOwnedError("hero does not own this item")
    if hero.level < item.template.level_requirement:
        raise LevelRequirementNotMetError("hero level is too low to equip this item")

    slot = item.template.slot
    currently_equipped = db.execute(
        select(ItemInstance).where(
            ItemInstance.owner_hero_id == hero.id,
            ItemInstance.equipped_slot == slot,
        )
    ).scalar_one_or_none()
    if currently_equipped is not None and currently_equipped.id != item.id:
        currently_equipped.equipped_slot = None
        db.add(currently_equipped)

    item.equipped_slot = slot
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def unequip_item(db: Session, hero: Hero, item_id: uuid.UUID) -> ItemInstance:
    item = db.get(ItemInstance, item_id)
    if item is None:
        raise ItemNotFoundError(f"item {item_id} not found")
    if item.owner_hero_id != hero.id:
        raise ItemNotOwnedError("hero does not own this item")

    item.equipped_slot = None
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def get_equipped_items(db: Session, hero: Hero) -> list[ItemInstance]:
    return (
        db.execute(
            select(ItemInstance).where(
                ItemInstance.owner_hero_id == hero.id,
                ItemInstance.equipped_slot.is_not(None),
            )
        )
        .scalars()
        .all()
    )


def get_owned_items(db: Session, hero: Hero) -> list[ItemInstance]:
    """Everything the hero owns, equipped or not (i.e. the full backpack)."""
    return (
        db.execute(
            select(ItemInstance)
            .where(ItemInstance.owner_hero_id == hero.id)
            .order_by(ItemInstance.acquired_at.desc())
        )
        .scalars()
        .all()
    )


def get_owned_materials(db: Session, hero: Hero) -> list[MaterialInstance]:
    """Every crafting-material stack the hero owns."""
    return (
        db.execute(
            select(MaterialInstance)
            .where(MaterialInstance.owner_hero_id == hero.id)
            .order_by(MaterialInstance.acquired_at.desc())
        )
        .scalars()
        .all()
    )
