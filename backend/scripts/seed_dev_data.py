"""Seed a handful of dev item/monster templates. Content data only, kept out
of Alembic migrations so migrations stay repeatable and diffable.

Run with: python -m scripts.seed_dev_data
"""

import re

from app.core.db import SessionLocal
from app.models.campaign import CampaignNode
from app.models.consumable import ConsumableTemplate
from app.models.crafting import CraftingRecipe, CraftingRecipeIngredient
from app.models.item import EquipmentSlot, ItemRarity, ItemTemplate
from app.models.material import MaterialTemplate
from app.models.monster import MonsterLootEntry, MonsterMaterialLootEntry, MonsterTemplate


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


# Just one worked example per template type (level 1 items, one monster's loot
# table) for the user to extend. Slugs are always derived from `name` via
# slugify() - never hand-typed.
ITEM_TEMPLATES = [
    # Tier1 gear set: defined through the weapon-damage/defense/bonus-HP
    # mechanics instead of flat stat bonuses (base_stats={}).
    dict(name="Wooden Stick", slot=EquipmentSlot.WEAPON, rarity=ItemRarity.COMMON, level_requirement=1, base_stats={}, damage_min=2, damage_max=6, description="Barely a weapon."),
    dict(name="Wooden Shield", slot=EquipmentSlot.SHIELD, rarity=ItemRarity.COMMON, level_requirement=1, base_stats={}, defense=3, description="Old wood and hide, but it holds."),
    dict(name="Leather Helm", slot=EquipmentSlot.HELMET, rarity=ItemRarity.COMMON, level_requirement=1, base_stats={}, defense=2, description="Better than nothing."),
    dict(name="Leather Robe", slot=EquipmentSlot.ARMOR, rarity=ItemRarity.COMMON, level_requirement=1, base_stats={}, defense=1, description="Thin leather, loosely stitched."),
    dict(name="Old Ring", slot=EquipmentSlot.AMULET, rarity=ItemRarity.COMMON, level_requirement=1, base_stats={}, bonus_max_hp=20, description="Worn smooth by someone else."),
]
for _item in ITEM_TEMPLATES:
    _item["slug"] = slugify(_item["name"])

MONSTER_TEMPLATES = [
    dict(
        name="Young Wolf",
        level_range_min=1,
        level_range_max=3,
        base_stats={"strength": 9, "dexterity": 11, "intelligence": 7, "vitality": 8, "agility": 10, "spirit": 10},
        flavor_text="Not quite a year old, and still testing its speed.",
        no_drop_weight=45,
    ),
]
for _monster in MONSTER_TEMPLATES:
    _monster["slug"] = slugify(_monster["name"])

MATERIAL_TEMPLATES = []
for _material in MATERIAL_TEMPLATES:
    _material["slug"] = slugify(_material["name"])

CONSUMABLE_TEMPLATES = []
for _consumable in CONSUMABLE_TEMPLATES:
    _consumable["slug"] = slugify(_consumable["name"])

CRAFTING_RECIPES = []
for _recipe in CRAFTING_RECIPES:
    _recipe["slug"] = slugify(_recipe["name"])

# Fixed, sequential battle nodes for the Campaign track. Slugs are hand-typed
# here (unlike items/monsters above) because they encode sequence order, not
# just the node name - slugify(name) alone would lose that.
# Empty for now - both nodes pinned to Veil Wisp, which was removed pending
# the user's first real enemy.
CAMPAIGN_NODES = []

# Young Wolf: each item weight 3 (sum 15), no_drop_weight 45 -> 75% nothing,
# 5% each item.
MONSTER_LOOT_ENTRIES = [
    dict(monster_slug=slugify("Young Wolf"), item_slug=slugify("Leather Helm"), drop_weight=3),
    dict(monster_slug=slugify("Young Wolf"), item_slug=slugify("Leather Robe"), drop_weight=3),
    dict(monster_slug=slugify("Young Wolf"), item_slug=slugify("Wooden Shield"), drop_weight=3),
    dict(monster_slug=slugify("Young Wolf"), item_slug=slugify("Wooden Stick"), drop_weight=3),
    dict(monster_slug=slugify("Young Wolf"), item_slug=slugify("Old Ring"), drop_weight=3),
]

MONSTER_MATERIAL_LOOT_ENTRIES = []


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
