import random
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.hero import Hero
from app.models.item import ItemTemplate
from app.models.material import MaterialTemplate
from app.models.monster import MonsterLootEntry, MonsterMaterialLootEntry, MonsterTemplate


def select_encounter(db: Session, hero: Hero, seed: int) -> dict[str, Any] | None:
    """Picks a monster eligible for the hero's level and builds its encounter payload.

    Uses a second, independent random.Random(seed) instance (not a shared RNG
    threaded into combat_engine.resolve) so monster selection stays
    reproducible from the same seed without entangling combat's own rolls.
    """
    templates = (
        db.execute(
            select(MonsterTemplate)
            .where(
                MonsterTemplate.level_range_min <= hero.level,
                MonsterTemplate.level_range_max >= hero.level,
            )
            .order_by(MonsterTemplate.slug)
        )
        .scalars()
        .all()
    )
    if not templates:
        return None

    monster = random.Random(seed).choice(templates)
    return build_encounter(db, monster)


def build_encounter(db: Session, monster: MonsterTemplate) -> dict[str, Any]:
    """Builds the encounter payload (stats + loot pools) for a specific monster."""
    loot_entries = (
        db.execute(
            select(MonsterLootEntry, ItemTemplate)
            .join(ItemTemplate, MonsterLootEntry.item_template_id == ItemTemplate.id)
            .where(MonsterLootEntry.monster_template_id == monster.id)
            .order_by(ItemTemplate.slug)
        )
        .all()
    )

    material_loot_entries = (
        db.execute(
            select(MonsterMaterialLootEntry, MaterialTemplate)
            .join(MaterialTemplate, MonsterMaterialLootEntry.material_template_id == MaterialTemplate.id)
            .where(MonsterMaterialLootEntry.monster_template_id == monster.id)
            .order_by(MaterialTemplate.slug)
        )
        .all()
    )

    return {
        "monster_slug": monster.slug,
        "monster_name": monster.name,
        "monster_stats": dict(monster.base_stats),
        "monster_level_min": monster.level_range_min,
        "monster_level_max": monster.level_range_max,
        "no_drop_weight": monster.no_drop_weight,
        "no_material_drop_weight": monster.no_material_drop_weight,
        "gold_min": monster.gold_min,
        "gold_max": monster.gold_max,
        "weapon_attack_min": monster.weapon_attack_min,
        "weapon_attack_max": monster.weapon_attack_max,
        "defense": monster.defense,
        "spell_attack_min": monster.spell_attack_min,
        "spell_attack_max": monster.spell_attack_max,
        "loot_pool": [
            {
                "item_template_slug": item.slug,
                "item_name": item.name,
                "drop_weight": float(entry.drop_weight),
            }
            for entry, item in loot_entries
        ],
        "material_pool": [
            {
                "material_template_slug": material.slug,
                "material_name": material.name,
                "drop_weight": float(entry.drop_weight),
            }
            for entry, material in material_loot_entries
        ],
    }
