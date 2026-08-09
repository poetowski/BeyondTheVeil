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
]
for _monster in MONSTER_TEMPLATES:
    _monster["slug"] = slugify(_monster["name"])

# Fixed, sequential battle nodes for the Campaign track. Slugs are hand-typed
# here (unlike items/monsters above) because they encode sequence order, not
# just the node name - slugify(name) alone would lose that.
CAMPAIGN_NODES = [
    dict(slug="campaign-01-wisp-threshold", order_index=1, name="The Wisp Threshold", required_level=1, gold_cost=0, monster_slug=slugify("Veil Wisp")),
    dict(slug="campaign-02-wisp-hollow", order_index=2, name="Wisp Hollow", required_level=2, gold_cost=10, monster_slug=slugify("Veil Wisp")),
]

# Dev drop table - Veil Wisp drops its full level-1 gear set.
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
