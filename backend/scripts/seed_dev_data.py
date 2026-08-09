"""Seed a handful of dev item/monster templates. Content data only, kept out
of Alembic migrations so migrations stay repeatable and diffable.

Run with: python -m scripts.seed_dev_data
"""

import re

from app.core.db import SessionLocal
from app.models.campaign import CampaignNode
from app.models.item import EquipmentSlot, ItemRarity, ItemTemplate
from app.models.monster import MonsterLootEntry, MonsterTemplate


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


# Just one worked example per template type (level 1 items, one monster's loot
# table) for the user to extend. Slugs are always derived from `name` via
# slugify() - never hand-typed.
ITEM_TEMPLATES = [
    dict(name="Fragment Shard Blade", slot=EquipmentSlot.WEAPON, rarity=ItemRarity.COMMON, level_requirement=1, base_stats={"strength": 2}),
    dict(name="Wisp-Touched Hood", slot=EquipmentSlot.HELMET, rarity=ItemRarity.COMMON, level_requirement=1, base_stats={"vitality": 1}),
    dict(name="Threshold Buckler", slot=EquipmentSlot.SHIELD, rarity=ItemRarity.COMMON, level_requirement=1, base_stats={"agility": 1}),
    dict(name="Fragment-Stitched Vest", slot=EquipmentSlot.ARMOR, rarity=ItemRarity.COMMON, level_requirement=1, base_stats={"vitality": 3}),
    dict(name="Drifting Charm", slot=EquipmentSlot.AMULET, rarity=ItemRarity.COMMON, level_requirement=1, base_stats={"spirit": 2}),
    dict(name="Wisp Spark", slot=EquipmentSlot.SPELL_SKILL, rarity=ItemRarity.COMMON, level_requirement=1, base_stats={"intelligence": 2}),
]
for _item in ITEM_TEMPLATES:
    _item["slug"] = slugify(_item["name"])

MONSTER_TEMPLATES = [
    dict(
        name="Veil Wisp",
        level_range_min=1,
        level_range_max=3,
        base_stats={"strength": 2, "dexterity": 3, "vitality": 4, "agility": 3, "intelligence": 2, "spirit": 2},
        flavor_text="A guttering flicker of the Veil's edge - more startled than hostile, until it isn't.",
    ),
    dict(
        name="Fragment Stalker",
        level_range_min=3,
        level_range_max=6,
        base_stats={"strength": 5, "dexterity": 4, "vitality": 8, "agility": 5, "intelligence": 1, "spirit": 1},
        flavor_text="It moves like something assembled in a hurry, all borrowed angles, hunting because that's what the fragment remembers being for.",
    ),
    dict(
        name="Hollow Warden",
        level_range_min=6,
        level_range_max=9,
        base_stats={"strength": 8, "dexterity": 6, "vitality": 14, "agility": 6, "intelligence": 3, "spirit": 3},
        flavor_text="Whatever it was guarding is long gone. It hasn't noticed yet.",
    ),
    dict(
        name="Veil Sovereign",
        level_range_min=10,
        level_range_max=14,
        base_stats={"strength": 12, "dexterity": 9, "vitality": 20, "agility": 9, "intelligence": 5, "spirit": 5},
        flavor_text="Not a ruler of anything - just the shape the Veil takes when a fragment refuses to end.",
    ),
]
for _monster in MONSTER_TEMPLATES:
    _monster["slug"] = slugify(_monster["name"])

# Fixed, sequential battle nodes for the Campaign track. Slugs are hand-typed
# here (unlike items/monsters above) because they encode sequence order, not
# just the node name - slugify(name) alone would lose that.
CAMPAIGN_NODES = [
    dict(slug="campaign-01-wisp-threshold", order_index=1, name="The Wisp Threshold", required_level=1, gold_cost=0, monster_slug=slugify("Veil Wisp")),
    dict(slug="campaign-02-wisp-hollow", order_index=2, name="Wisp Hollow", required_level=2, gold_cost=10, monster_slug=slugify("Veil Wisp")),
    dict(slug="campaign-03-stalkers-approach", order_index=3, name="Stalker's Approach", required_level=3, gold_cost=25, monster_slug=slugify("Fragment Stalker")),
    dict(slug="campaign-04-fragment-maze", order_index=4, name="Fragment Maze", required_level=5, gold_cost=50, monster_slug=slugify("Fragment Stalker")),
    dict(slug="campaign-05-hollow-wardens-gate", order_index=5, name="Hollow Warden's Gate", required_level=7, gold_cost=100, monster_slug=slugify("Hollow Warden")),
    dict(slug="campaign-06-veil-sovereign", order_index=6, name="The Veil Sovereign", required_level=10, gold_cost=200, monster_slug=slugify("Veil Sovereign")),
]

# Dev drop table - one worked example (Veil Wisp drops its full level-1 gear
# set). The other monsters have no loot yet; add more as items are added.
MONSTER_LOOT_ENTRIES = [
    dict(monster_slug=slugify("Veil Wisp"), item_slug=slugify("Fragment Shard Blade"), drop_weight=5),
    dict(monster_slug=slugify("Veil Wisp"), item_slug=slugify("Wisp-Touched Hood"), drop_weight=5),
    dict(monster_slug=slugify("Veil Wisp"), item_slug=slugify("Threshold Buckler"), drop_weight=4),
    dict(monster_slug=slugify("Veil Wisp"), item_slug=slugify("Fragment-Stitched Vest"), drop_weight=3),
    dict(monster_slug=slugify("Veil Wisp"), item_slug=slugify("Drifting Charm"), drop_weight=3),
    dict(monster_slug=slugify("Veil Wisp"), item_slug=slugify("Wisp Spark"), drop_weight=3),
]


def seed() -> None:
    db = SessionLocal()
    try:
        for data in ITEM_TEMPLATES:
            if db.query(ItemTemplate).filter_by(slug=data["slug"]).first():
                continue
            db.add(ItemTemplate(**data))

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
