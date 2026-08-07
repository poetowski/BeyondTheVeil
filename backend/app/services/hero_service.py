from app.models.hero import Hero
from app.models.item import ItemInstance

STAT_NAMES = ("strength", "dexterity", "vitality", "agility", "intelligence", "spirit")

HP_PER_VITALITY = 10
BASE_HP = 50


def compute_effective_stats(hero: Hero, equipped_items: list[ItemInstance]) -> dict[str, int]:
    """Base hero stats plus bonuses from every currently-equipped item."""
    effective = {stat: getattr(hero, stat) for stat in STAT_NAMES}
    for item in equipped_items:
        if item.equipped_slot is None:
            continue
        for source in (item.template.base_stats, item.rolled_stats):
            if not source:
                continue
            for stat, bonus in source.items():
                if stat in effective:
                    effective[stat] += bonus
    return effective


def compute_max_hp(effective_vitality: int) -> int:
    """Placeholder formula; combat balance is a separate future task."""
    return BASE_HP + effective_vitality * HP_PER_VITALITY
