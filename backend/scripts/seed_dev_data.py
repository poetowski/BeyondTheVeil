"""Seed a handful of dev item/monster templates. Content data only, kept out
of Alembic migrations so migrations stay repeatable and diffable.

Run with: python -m scripts.seed_dev_data
"""

from app.core.db import SessionLocal
from app.models.campaign import CampaignNode
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
    dict(
        slug="hollow-warden",
        name="Hollow Warden",
        level_range_min=6,
        level_range_max=9,
        base_stats={"strength": 8, "dexterity": 6, "vitality": 14, "agility": 6, "intelligence": 3, "spirit": 3},
    ),
    dict(
        slug="veil-sovereign",
        name="Veil Sovereign",
        level_range_min=10,
        level_range_max=14,
        base_stats={"strength": 12, "dexterity": 9, "vitality": 20, "agility": 9, "intelligence": 5, "spirit": 5},
    ),
]

# Fixed, sequential battle nodes for the Campaign track. Only the first is
# reachable today (required_level=1, gold_cost=0) — gold has no earn source
# yet and leveling doesn't exist, so nodes 2+ are legitimately unreachable
# until those systems land, matching the same "real system, empty for now"
# pattern used for Materials.
CAMPAIGN_NODES = [
    dict(slug="campaign-01-wisp-threshold", order_index=1, name="The Wisp Threshold", required_level=1, gold_cost=0, monster_slug="veil-wisp"),
    dict(slug="campaign-02-wisp-hollow", order_index=2, name="Wisp Hollow", required_level=2, gold_cost=10, monster_slug="veil-wisp"),
    dict(slug="campaign-03-stalkers-approach", order_index=3, name="Stalker's Approach", required_level=3, gold_cost=25, monster_slug="fragment-stalker"),
    dict(slug="campaign-04-fragment-maze", order_index=4, name="Fragment Maze", required_level=5, gold_cost=50, monster_slug="fragment-stalker"),
    dict(slug="campaign-05-hollow-wardens-gate", order_index=5, name="Hollow Warden's Gate", required_level=7, gold_cost=100, monster_slug="hollow-warden"),
    dict(slug="campaign-06-veil-sovereign", order_index=6, name="The Veil Sovereign", required_level=10, gold_cost=200, monster_slug="veil-sovereign"),
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

        db.flush()

        for data in CAMPAIGN_NODES:
            if db.query(CampaignNode).filter_by(slug=data["slug"]).first():
                continue
            monster = db.query(MonsterTemplate).filter_by(slug=data["monster_slug"]).first()
            db.add(
                CampaignNode(
                    slug=data["slug"],
                    order_index=data["order_index"],
                    name=data["name"],
                    required_level=data["required_level"],
                    gold_cost=data["gold_cost"],
                    monster_template_id=monster.id,
                )
            )

        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    seed()
