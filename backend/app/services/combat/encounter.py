import random
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.hero import Hero
from app.models.item import ItemTemplate
from app.models.monster import MonsterLootEntry, MonsterTemplate


def select_encounter(db: Session, hero: Hero, seed: int) -> dict[str, Any] | None:
    """Picks a monster eligible for the hero's level and its loot pool.

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

    loot_entries = (
        db.execute(
            select(MonsterLootEntry, ItemTemplate)
            .join(ItemTemplate, MonsterLootEntry.item_template_id == ItemTemplate.id)
            .where(MonsterLootEntry.monster_template_id == monster.id)
            .order_by(ItemTemplate.slug)
        )
        .all()
    )

    return {
        "monster_slug": monster.slug,
        "monster_name": monster.name,
        "monster_stats": dict(monster.base_stats),
        "loot_pool": [
            {
                "item_template_slug": item.slug,
                "item_name": item.name,
                "drop_weight": float(entry.drop_weight),
            }
            for entry, item in loot_entries
        ],
    }
