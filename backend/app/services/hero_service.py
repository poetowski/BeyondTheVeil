from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.hero import Hero
from app.models.item import ItemInstance
from app.models.material import MaterialInstance

STAT_NAMES = ("strength", "dexterity", "intelligence", "vitality", "agility", "spirit")

HP_PER_VITALITY = 10
BASE_HP = 50
BASELINE_STAT_VALUE = 10

STAT_POINTS_PER_LEVEL = 3
XP_PER_LEVEL_STEP = 100


class InvalidStatError(ValueError):
    pass


class InsufficientStatPointsError(ValueError):
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
    """Cumulative XP needed to *reach* `level` (level 1 = 0 XP). XP needed to
    go from level L to L+1 is 100*L, so this is the triangular-number sum."""
    return XP_PER_LEVEL_STEP * (level - 1) * level // 2


def apply_level_ups(hero: Hero) -> None:
    """Repeatedly levels the hero up while accumulated XP clears the next
    threshold, so a single large XP reward can cross multiple levels at once.
    Each level grants STAT_POINTS_PER_LEVEL unallocated stat points."""
    while hero.xp >= xp_required_for_level(hero.level + 1):
        hero.level += 1
        hero.available_stat_points += STAT_POINTS_PER_LEVEL


def xp_progress(hero: Hero) -> tuple[int, int]:
    """(xp earned into the current level, xp needed for the current level) —
    for a per-level progress readout, not raw cumulative totals."""
    floor = xp_required_for_level(hero.level)
    ceiling = xp_required_for_level(hero.level + 1)
    return hero.xp - floor, ceiling - floor


def allocate_stat_point(hero: Hero, stat: str, amount: int) -> None:
    if stat not in STAT_NAMES:
        raise InvalidStatError(f"unknown stat {stat!r}")
    if amount <= 0:
        raise InvalidStatError("amount must be positive")
    if hero.available_stat_points < amount:
        raise InsufficientStatPointsError("not enough stat points")
    setattr(hero, stat, getattr(hero, stat) + amount)
    hero.available_stat_points -= amount


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
