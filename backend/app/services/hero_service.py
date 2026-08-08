from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.hero import Hero
from app.models.item import ItemInstance

STAT_NAMES = ("strength", "dexterity", "intelligence", "vitality", "agility", "spirit")

HP_PER_VITALITY = 10
BASE_HP = 50
BASELINE_STAT_VALUE = 10


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
