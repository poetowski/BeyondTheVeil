"""Seed a handful of dev item/monster templates. Content data only, kept out
of Alembic migrations so migrations stay repeatable and diffable.

Run with: python -m scripts.seed_dev_data
"""

from app.core.db import SessionLocal
from app.models.item import EquipmentSlot, ItemRarity, ItemTemplate
from app.models.monster import MonsterLootEntry, MonsterTemplate

ITEM_TEMPLATES = [
    dict(slug="rusty-sword", name="Rusty Sword", slot=EquipmentSlot.WEAPON, base_stats={"strength": 2}),
    dict(slug="leather-cap", name="Leather Cap", slot=EquipmentSlot.HELMET, base_stats={"vitality": 1}),
    dict(slug="wooden-buckler", name="Wooden Buckler", slot=EquipmentSlot.SHIELD, base_stats={"agility": 1}),
    dict(slug="padded-armor", name="Padded Armor", slot=EquipmentSlot.ARMOR, base_stats={"vitality": 3}),
    dict(slug="copper-amulet", name="Copper Amulet", slot=EquipmentSlot.AMULET, base_stats={"spirit": 2}),
    dict(slug="spark-cantrip", name="Spark Cantrip", slot=EquipmentSlot.SPELL_SKILL, base_stats={"intelligence": 2}),
]

MONSTER_TEMPLATES = [
    dict(
        slug="veil-wisp",
        name="Veil Wisp",
        level_range_min=1,
        level_range_max=3,
        base_stats={"strength": 2, "dexterity": 3, "vitality": 4, "agility": 3, "intelligence": 2, "spirit": 2},
    ),
    dict(
        slug="fragment-stalker",
        name="Fragment Stalker",
        # Unreachable content until a leveling system exists (nothing increments
        # Hero.level anywhere today, so every hero is level 1) — seeded anyway
        # for forward-compat, not scope creep into building leveling now.
        level_range_min=3,
        level_range_max=6,
        base_stats={"strength": 5, "dexterity": 4, "vitality": 8, "agility": 5, "intelligence": 1, "spirit": 1},
    ),
]

# Dev/placeholder drop tables, not final balance. spark-cantrip is deliberately
# excluded from both — intelligence is dormant in v1 physical-only combat, so a
# spell drop would be dead flavor right now.
MONSTER_LOOT_ENTRIES = [
    dict(monster_slug="veil-wisp", item_slug="leather-cap", drop_weight=5),
    dict(monster_slug="veil-wisp", item_slug="wooden-buckler", drop_weight=5),
    dict(monster_slug="veil-wisp", item_slug="rusty-sword", drop_weight=2),
    dict(monster_slug="fragment-stalker", item_slug="padded-armor", drop_weight=4),
    dict(monster_slug="fragment-stalker", item_slug="rusty-sword", drop_weight=3),
    dict(monster_slug="fragment-stalker", item_slug="copper-amulet", drop_weight=2),
    dict(monster_slug="fragment-stalker", item_slug="leather-cap", drop_weight=1),
]


def seed() -> None:
    db = SessionLocal()
    try:
        for data in ITEM_TEMPLATES:
            if db.query(ItemTemplate).filter_by(slug=data["slug"]).first():
                continue
            db.add(ItemTemplate(rarity=ItemRarity.COMMON, **data))

        for data in MONSTER_TEMPLATES:
            if db.query(MonsterTemplate).filter_by(slug=data["slug"]).first():
                continue
            db.add(MonsterTemplate(**data))

        db.flush()

        for entry in MONSTER_LOOT_ENTRIES:
            monster = db.query(MonsterTemplate).filter_by(slug=entry["monster_slug"]).first()
            item = db.query(ItemTemplate).filter_by(slug=entry["item_slug"]).first()
            if monster is None or item is None:
                continue
            exists = (
                db.query(MonsterLootEntry)
                .filter_by(monster_template_id=monster.id, item_template_id=item.id)
                .first()
            )
            if exists:
                continue
            db.add(
                MonsterLootEntry(
                    monster_template_id=monster.id,
                    item_template_id=item.id,
                    drop_weight=entry["drop_weight"],
                )
            )

        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    seed()
