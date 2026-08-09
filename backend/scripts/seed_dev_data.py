"""Seed a handful of dev item/monster templates. Content data only, kept out
of Alembic migrations so migrations stay repeatable and diffable.

Run with: python -m scripts.seed_dev_data
"""

from app.core.db import SessionLocal
from app.models.campaign import CampaignNode
from app.models.item import EquipmentSlot, ItemRarity, ItemTemplate
from app.models.monster import MonsterLootEntry, MonsterTemplate

ITEM_TEMPLATES = [
    # Tier 1 - Fragment-born (common, veil-wisp drops)
    dict(slug="fragment-shard-blade", name="Fragment Shard Blade", slot=EquipmentSlot.WEAPON, rarity=ItemRarity.COMMON, level_requirement=1, base_stats={"strength": 2}),
    dict(slug="wisp-touched-hood", name="Wisp-Touched Hood", slot=EquipmentSlot.HELMET, rarity=ItemRarity.COMMON, level_requirement=1, base_stats={"vitality": 1}),
    dict(slug="threshold-buckler", name="Threshold Buckler", slot=EquipmentSlot.SHIELD, rarity=ItemRarity.COMMON, level_requirement=1, base_stats={"agility": 1}),
    dict(slug="fragment-stitched-vest", name="Fragment-Stitched Vest", slot=EquipmentSlot.ARMOR, rarity=ItemRarity.COMMON, level_requirement=1, base_stats={"vitality": 3}),
    dict(slug="drifting-charm", name="Drifting Charm", slot=EquipmentSlot.AMULET, rarity=ItemRarity.COMMON, level_requirement=1, base_stats={"spirit": 2}),
    dict(slug="wisp-spark", name="Wisp Spark", slot=EquipmentSlot.SPELL_SKILL, rarity=ItemRarity.COMMON, level_requirement=1, base_stats={"intelligence": 2}),
    # Tier 2 - Hollowed (uncommon, fragment-stalker drops)
    dict(slug="hollow-fang", name="Hollow Fang", slot=EquipmentSlot.WEAPON, rarity=ItemRarity.UNCOMMON, level_requirement=3, base_stats={"strength": 4}),
    dict(slug="stalkers-mask", name="Stalker's Mask", slot=EquipmentSlot.HELMET, rarity=ItemRarity.UNCOMMON, level_requirement=3, base_stats={"vitality": 2}),
    dict(slug="splintered-ward", name="Splintered Ward", slot=EquipmentSlot.SHIELD, rarity=ItemRarity.UNCOMMON, level_requirement=3, base_stats={"agility": 2}),
    dict(slug="husk-plate", name="Husk Plate", slot=EquipmentSlot.ARMOR, rarity=ItemRarity.UNCOMMON, level_requirement=3, base_stats={"vitality": 5}),
    dict(slug="echo-loop", name="Echo Loop", slot=EquipmentSlot.AMULET, rarity=ItemRarity.UNCOMMON, level_requirement=3, base_stats={"spirit": 4}),
    dict(slug="fracture-rune", name="Fracture Rune", slot=EquipmentSlot.SPELL_SKILL, rarity=ItemRarity.UNCOMMON, level_requirement=3, base_stats={"intelligence": 4}),
    # Tier 3 - Warden-forged (rare, hollow-warden drops)
    dict(slug="wardens-greatblade", name="Warden's Greatblade", slot=EquipmentSlot.WEAPON, rarity=ItemRarity.RARE, level_requirement=6, base_stats={"strength": 7}),
    dict(slug="sentinel-crown", name="Sentinel Crown", slot=EquipmentSlot.HELMET, rarity=ItemRarity.RARE, level_requirement=6, base_stats={"vitality": 4}),
    dict(slug="bastion-aegis", name="Bastion Aegis", slot=EquipmentSlot.SHIELD, rarity=ItemRarity.RARE, level_requirement=6, base_stats={"agility": 4}),
    dict(slug="wardplate", name="Wardplate", slot=EquipmentSlot.ARMOR, rarity=ItemRarity.RARE, level_requirement=6, base_stats={"vitality": 9}),
    dict(slug="vigil-sigil", name="Vigil Sigil", slot=EquipmentSlot.AMULET, rarity=ItemRarity.RARE, level_requirement=6, base_stats={"spirit": 7}),
    dict(slug="wardens-grimoire", name="Warden's Grimoire", slot=EquipmentSlot.SPELL_SKILL, rarity=ItemRarity.RARE, level_requirement=6, base_stats={"intelligence": 7}),
    # Tier 4 - Sovereign (epic, veil-sovereign drops)
    dict(slug="sovereigns-edge", name="Sovereign's Edge", slot=EquipmentSlot.WEAPON, rarity=ItemRarity.EPIC, level_requirement=10, base_stats={"strength": 10}),
    dict(slug="crown-of-the-unmade", name="Crown of the Unmade", slot=EquipmentSlot.HELMET, rarity=ItemRarity.EPIC, level_requirement=10, base_stats={"vitality": 6}),
    dict(slug="absolute-ward", name="Absolute Ward", slot=EquipmentSlot.SHIELD, rarity=ItemRarity.EPIC, level_requirement=10, base_stats={"agility": 6}),
    dict(slug="sovereign-carapace", name="Sovereign Carapace", slot=EquipmentSlot.ARMOR, rarity=ItemRarity.EPIC, level_requirement=10, base_stats={"vitality": 13}),
    dict(slug="seal-of-the-veil", name="Seal of the Veil", slot=EquipmentSlot.AMULET, rarity=ItemRarity.EPIC, level_requirement=10, base_stats={"spirit": 10}),
    dict(slug="sovereigns-cataclysm", name="Sovereign's Cataclysm", slot=EquipmentSlot.SPELL_SKILL, rarity=ItemRarity.EPIC, level_requirement=10, base_stats={"intelligence": 10}),
    # Legendary capstone - veil-sovereign exclusive, low drop weight
    dict(slug="heartshard-of-the-veil", name="Heartshard of the Veil", slot=EquipmentSlot.WEAPON, rarity=ItemRarity.LEGENDARY, level_requirement=10, base_stats={"strength": 14, "intelligence": 6}),
]

MONSTER_TEMPLATES = [
    dict(
        slug="veil-wisp",
        name="Veil Wisp",
        level_range_min=1,
        level_range_max=3,
        base_stats={"strength": 2, "dexterity": 3, "vitality": 4, "agility": 3, "intelligence": 2, "spirit": 2},
        flavor_text="A guttering flicker of the Veil's edge - more startled than hostile, until it isn't.",
    ),
    dict(
        slug="fragment-stalker",
        name="Fragment Stalker",
        level_range_min=3,
        level_range_max=6,
        base_stats={"strength": 5, "dexterity": 4, "vitality": 8, "agility": 5, "intelligence": 1, "spirit": 1},
        flavor_text="It moves like something assembled in a hurry, all borrowed angles, hunting because that's what the fragment remembers being for.",
    ),
    dict(
        slug="hollow-warden",
        name="Hollow Warden",
        level_range_min=6,
        level_range_max=9,
        base_stats={"strength": 8, "dexterity": 6, "vitality": 14, "agility": 6, "intelligence": 3, "spirit": 3},
        flavor_text="Whatever it was guarding is long gone. It hasn't noticed yet.",
    ),
    dict(
        slug="veil-sovereign",
        name="Veil Sovereign",
        level_range_min=10,
        level_range_max=14,
        base_stats={"strength": 12, "dexterity": 9, "vitality": 20, "agility": 9, "intelligence": 5, "spirit": 5},
        flavor_text="Not a ruler of anything - just the shape the Veil takes when a fragment refuses to end.",
    ),
]

# Fixed, sequential battle nodes for the Campaign track.
CAMPAIGN_NODES = [
    dict(slug="campaign-01-wisp-threshold", order_index=1, name="The Wisp Threshold", required_level=1, gold_cost=0, monster_slug="veil-wisp"),
    dict(slug="campaign-02-wisp-hollow", order_index=2, name="Wisp Hollow", required_level=2, gold_cost=10, monster_slug="veil-wisp"),
    dict(slug="campaign-03-stalkers-approach", order_index=3, name="Stalker's Approach", required_level=3, gold_cost=25, monster_slug="fragment-stalker"),
    dict(slug="campaign-04-fragment-maze", order_index=4, name="Fragment Maze", required_level=5, gold_cost=50, monster_slug="fragment-stalker"),
    dict(slug="campaign-05-hollow-wardens-gate", order_index=5, name="Hollow Warden's Gate", required_level=7, gold_cost=100, monster_slug="hollow-warden"),
    dict(slug="campaign-06-veil-sovereign", order_index=6, name="The Veil Sovereign", required_level=10, gold_cost=200, monster_slug="veil-sovereign"),
]

# Dev drop tables, not final balance. Each monster drops the full gear set of
# its matching tier; the veil-sovereign additionally has a rare chance at the
# legendary capstone weapon.
MONSTER_LOOT_ENTRIES = [
    dict(monster_slug="veil-wisp", item_slug="fragment-shard-blade", drop_weight=5),
    dict(monster_slug="veil-wisp", item_slug="wisp-touched-hood", drop_weight=5),
    dict(monster_slug="veil-wisp", item_slug="threshold-buckler", drop_weight=4),
    dict(monster_slug="veil-wisp", item_slug="fragment-stitched-vest", drop_weight=3),
    dict(monster_slug="veil-wisp", item_slug="drifting-charm", drop_weight=3),
    dict(monster_slug="veil-wisp", item_slug="wisp-spark", drop_weight=3),
    dict(monster_slug="fragment-stalker", item_slug="hollow-fang", drop_weight=5),
    dict(monster_slug="fragment-stalker", item_slug="stalkers-mask", drop_weight=4),
    dict(monster_slug="fragment-stalker", item_slug="splintered-ward", drop_weight=4),
    dict(monster_slug="fragment-stalker", item_slug="husk-plate", drop_weight=3),
    dict(monster_slug="fragment-stalker", item_slug="echo-loop", drop_weight=3),
    dict(monster_slug="fragment-stalker", item_slug="fracture-rune", drop_weight=3),
    dict(monster_slug="hollow-warden", item_slug="wardens-greatblade", drop_weight=5),
    dict(monster_slug="hollow-warden", item_slug="sentinel-crown", drop_weight=4),
    dict(monster_slug="hollow-warden", item_slug="bastion-aegis", drop_weight=4),
    dict(monster_slug="hollow-warden", item_slug="wardplate", drop_weight=3),
    dict(monster_slug="hollow-warden", item_slug="vigil-sigil", drop_weight=3),
    dict(monster_slug="hollow-warden", item_slug="wardens-grimoire", drop_weight=3),
    dict(monster_slug="veil-sovereign", item_slug="sovereigns-edge", drop_weight=5),
    dict(monster_slug="veil-sovereign", item_slug="crown-of-the-unmade", drop_weight=4),
    dict(monster_slug="veil-sovereign", item_slug="absolute-ward", drop_weight=4),
    dict(monster_slug="veil-sovereign", item_slug="sovereign-carapace", drop_weight=3),
    dict(monster_slug="veil-sovereign", item_slug="seal-of-the-veil", drop_weight=3),
    dict(monster_slug="veil-sovereign", item_slug="sovereigns-cataclysm", drop_weight=3),
    dict(monster_slug="veil-sovereign", item_slug="heartshard-of-the-veil", drop_weight=1),
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
