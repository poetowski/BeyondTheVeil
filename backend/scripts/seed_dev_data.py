"""Seed a handful of dev item/monster templates. Content data only, kept out
of Alembic migrations so migrations stay repeatable and diffable.

Run with: python -m scripts.seed_dev_data
"""

import re

from app.core.db import SessionLocal
from app.models.campaign import CampaignNode
from app.models.consumable import ConsumableTemplate
from app.models.crafting import CraftingCategory, CraftingRecipe, CraftingRecipeIngredient
from app.models.item import EquipmentSlot, ItemRarity, ItemTemplate
from app.models.material import MaterialTemplate
from app.models.monster import MonsterLootEntry, MonsterMaterialLootEntry, MonsterTemplate


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
    # Tier1 gear set: defined through the weapon-damage/defense/bonus-HP
    # mechanics instead of flat stat bonuses (base_stats={}).
    dict(name="Wooden Stick", slot=EquipmentSlot.WEAPON, rarity=ItemRarity.COMMON, level_requirement=1, base_stats={}, damage_min=2, damage_max=6),
    dict(name="Wooden Shield", slot=EquipmentSlot.SHIELD, rarity=ItemRarity.COMMON, level_requirement=1, base_stats={}, defense=3),
    dict(name="Leather Helm", slot=EquipmentSlot.HELMET, rarity=ItemRarity.COMMON, level_requirement=1, base_stats={}, defense=2),
    dict(name="Leather Robe", slot=EquipmentSlot.ARMOR, rarity=ItemRarity.COMMON, level_requirement=1, base_stats={}, defense=1),
    dict(name="Old Ring", slot=EquipmentSlot.AMULET, rarity=ItemRarity.COMMON, level_requirement=1, base_stats={}, bonus_max_hp=20),
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

MATERIAL_TEMPLATES = [
    dict(
        name="Wisp Residue",
        description="A faintly luminous residue left behind when a Veil Wisp is struck down.",
        category=CraftingCategory.ALCHEMY,
    ),
]
for _material in MATERIAL_TEMPLATES:
    _material["slug"] = slugify(_material["name"])

CONSUMABLE_TEMPLATES = [
    dict(name="Minor Healing Elixir", description="A quick brew that mends shallow wounds.", heal_amount_fraction=0.3),
]
for _consumable in CONSUMABLE_TEMPLATES:
    _consumable["slug"] = slugify(_consumable["name"])

# One worked example Alchemy recipe, craftable from level 1.
CRAFTING_RECIPES = [
    dict(
        name="Minor Healing Elixir",
        category=CraftingCategory.ALCHEMY,
        level_requirement=1,
        output_consumable_slug=slugify("Minor Healing Elixir"),
        output_quantity=1,
        ingredients=[dict(material_slug=slugify("Wisp Residue"), quantity_required=3)],
    ),
]
for _recipe in CRAFTING_RECIPES:
    _recipe["slug"] = slugify(_recipe["name"])

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

MONSTER_MATERIAL_LOOT_ENTRIES = [
    dict(monster_slug=slugify("Veil Wisp"), material_slug=slugify("Wisp Residue"), drop_weight=5),
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

        for data in MATERIAL_TEMPLATES:
            if db.query(MaterialTemplate).filter_by(slug=data["slug"]).first():
                continue
            db.add(MaterialTemplate(**data))

        for data in CONSUMABLE_TEMPLATES:
            if db.query(ConsumableTemplate).filter_by(slug=data["slug"]).first():
                continue
            db.add(ConsumableTemplate(**data))

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

        for entry in MONSTER_MATERIAL_LOOT_ENTRIES:
            monster = db.query(MonsterTemplate).filter_by(slug=entry["monster_slug"]).first()
            material = db.query(MaterialTemplate).filter_by(slug=entry["material_slug"]).first()
            if monster is None or material is None:
                continue
            exists = (
                db.query(MonsterMaterialLootEntry)
                .filter_by(monster_template_id=monster.id, material_template_id=material.id)
                .first()
            )
            if exists:
                continue
            db.add(
                MonsterMaterialLootEntry(
                    monster_template_id=monster.id,
                    material_template_id=material.id,
                    drop_weight=entry["drop_weight"],
                )
            )

        for data in CRAFTING_RECIPES:
            if db.query(CraftingRecipe).filter_by(slug=data["slug"]).first():
                continue
            output_consumable = (
                db.query(ConsumableTemplate).filter_by(slug=data["output_consumable_slug"]).first()
            )
            if output_consumable is None:
                continue
            recipe = CraftingRecipe(
                slug=data["slug"],
                name=data["name"],
                category=data["category"],
                level_requirement=data["level_requirement"],
                output_consumable_template_id=output_consumable.id,
                output_quantity=data["output_quantity"],
            )
            db.add(recipe)
            db.flush()
            for ingredient in data["ingredients"]:
                material = db.query(MaterialTemplate).filter_by(slug=ingredient["material_slug"]).first()
                if material is None:
                    continue
                db.add(
                    CraftingRecipeIngredient(
                        recipe_id=recipe.id,
                        material_template_id=material.id,
                        quantity_required=ingredient["quantity_required"],
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
