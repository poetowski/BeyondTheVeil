"""Seed a handful of dev item/monster templates. Content data only, kept out
of Alembic migrations so migrations stay repeatable and diffable.

Run with: python -m scripts.seed_dev_data
"""

import re

from app.core.db import SessionLocal
from app.models.consumable import ConsumableTemplate
from app.models.crafting import CraftingCategory, CraftingRecipe, CraftingRecipeIngredient
from app.models.item import EquipmentSlot, ItemRarity, ItemTemplate
from app.models.material import MaterialTemplate
from app.models.monster import MonsterLootEntry, MonsterMaterialLootEntry, MonsterTemplate
from app.models.rune import RuneTemplate


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
        no_material_drop_weight=70,
        gold_min=8,
        gold_max=20,
        weapon_attack_min=2,
        weapon_attack_max=4,
        defense=1,
        spell_attack_min=0,
        spell_attack_max=1,
    ),
    dict(
        name="Veil Wisp",
        level_range_min=1,
        level_range_max=3,
        base_stats={"strength": 5, "dexterity": 9, "intelligence": 12, "vitality": 6, "agility": 11, "spirit": 12},
        flavor_text="A knot of veil-light that hasn't decided if it's alive. It drifts until something moves too close, then it isn't drifting anymore.",
        no_material_drop_weight=30,
        gold_min=15,
        gold_max=30,
        weapon_attack_min=1,
        weapon_attack_max=3,
        defense=0,
        spell_attack_min=2,
        spell_attack_max=4,
    ),
]
for _monster in MONSTER_TEMPLATES:
    _monster["slug"] = slugify(_monster["name"])

MATERIAL_TEMPLATES = [
    dict(name="Plantago", description="Broad leaves, bruised for their sap.", category=CraftingCategory.ALCHEMY),
    dict(name="Chamomile", description="Daisy-like flowers, dried for their mild sedative properties.", category=CraftingCategory.ALCHEMY),
    dict(name="Iron Ore", description="Rough-smelted lumps, still warm from the earth.", category=CraftingCategory.FORGE),
    dict(name="Tin Shard", description="Bright, brittle fragments that ring when struck.", category=CraftingCategory.FORGE),
    dict(name="Ember Dust", description="Fine grey ash from a forge fire, still faintly hot.", category=CraftingCategory.FORGE),
]
for _material in MATERIAL_TEMPLATES:
    _material["slug"] = slugify(_material["name"])

RUNE_TEMPLATES = [
    dict(name="Rune of Vigor", description="A dull red glyph, warm to the touch.", stat_bonuses={"vitality": 3}),
    dict(name="Rune of Might", description="A jagged glyph that seems to strain against its own edges.", stat_bonuses={"strength": 3}),
]
for _rune in RUNE_TEMPLATES:
    _rune["slug"] = slugify(_rune["name"])

CONSUMABLE_TEMPLATES = [
    dict(
        name="Minor Healing Potion",
        description="A cloudy brew of crushed herbs, drunk quickly before it settles.",
        heal_flat=100,
        heal_vitality_multiplier=2,
    ),
]
for _consumable in CONSUMABLE_TEMPLATES:
    _consumable["slug"] = slugify(_consumable["name"])

# Two alternative recipes for the same potion.
CRAFTING_RECIPES = [
    dict(
        name="Minor Healing Potion (Plantago Blend)",
        category=CraftingCategory.ALCHEMY,
        level_requirement=1,
        output_consumable_slug=slugify("Minor Healing Potion"),
        output_quantity=1,
        ingredients=[
            dict(material_slug=slugify("Plantago"), quantity_required=2),
            dict(material_slug=slugify("Chamomile"), quantity_required=3),
        ],
    ),
    dict(
        name="Minor Healing Potion (Chamomile Only)",
        category=CraftingCategory.ALCHEMY,
        level_requirement=1,
        output_consumable_slug=slugify("Minor Healing Potion"),
        output_quantity=1,
        ingredients=[dict(material_slug=slugify("Chamomile"), quantity_required=6)],
    ),
    dict(
        name="Rune of Vigor",
        category=CraftingCategory.FORGE,
        level_requirement=1,
        output_rune_slug=slugify("Rune of Vigor"),
        output_quantity=1,
        ingredients=[
            dict(material_slug=slugify("Iron Ore"), quantity_required=3),
            dict(material_slug=slugify("Ember Dust"), quantity_required=2),
        ],
    ),
    dict(
        name="Rune of Might",
        category=CraftingCategory.FORGE,
        level_requirement=1,
        output_rune_slug=slugify("Rune of Might"),
        output_quantity=1,
        ingredients=[
            dict(material_slug=slugify("Tin Shard"), quantity_required=3),
            dict(material_slug=slugify("Ember Dust"), quantity_required=2),
        ],
    ),
]
for _recipe in CRAFTING_RECIPES:
    _recipe["slug"] = slugify(_recipe["name"])

# Young Wolf: each item weight 3 (sum 15), no_drop_weight 45 -> 75% nothing,
# 5% each item.
MONSTER_LOOT_ENTRIES = [
    dict(monster_slug=slugify("Young Wolf"), item_slug=slugify("Leather Helm"), drop_weight=3),
    dict(monster_slug=slugify("Young Wolf"), item_slug=slugify("Leather Robe"), drop_weight=3),
    dict(monster_slug=slugify("Young Wolf"), item_slug=slugify("Wooden Shield"), drop_weight=3),
    dict(monster_slug=slugify("Young Wolf"), item_slug=slugify("Wooden Stick"), drop_weight=3),
    dict(monster_slug=slugify("Young Wolf"), item_slug=slugify("Old Ring"), drop_weight=3),
]

# Young Wolf: no_material_drop_weight 70, Chamomile 20, Plantago 10 -> 70%
# nothing, 20% Chamomile, 10% Plantago.
# Veil Wisp: no_material_drop_weight 30, Chamomile 45, Plantago 25 -> 30%
# nothing, 45% Chamomile, 25% Plantago (higher than Young Wolf's since Veil
# Wisp has no item loot table at all).
# Forge materials (Iron Ore, Tin Shard, Ember Dust) are added to both
# monsters' tables at weights comparable to their existing Alchemy drops -
# without a drop source Forge recipes would be craftable in name only.
MONSTER_MATERIAL_LOOT_ENTRIES = [
    dict(monster_slug=slugify("Young Wolf"), material_slug=slugify("Chamomile"), drop_weight=20),
    dict(monster_slug=slugify("Young Wolf"), material_slug=slugify("Plantago"), drop_weight=10),
    dict(monster_slug=slugify("Young Wolf"), material_slug=slugify("Iron Ore"), drop_weight=15),
    dict(monster_slug=slugify("Young Wolf"), material_slug=slugify("Tin Shard"), drop_weight=10),
    dict(monster_slug=slugify("Young Wolf"), material_slug=slugify("Ember Dust"), drop_weight=8),
    dict(monster_slug=slugify("Veil Wisp"), material_slug=slugify("Chamomile"), drop_weight=45),
    dict(monster_slug=slugify("Veil Wisp"), material_slug=slugify("Plantago"), drop_weight=25),
    dict(monster_slug=slugify("Veil Wisp"), material_slug=slugify("Iron Ore"), drop_weight=15),
    dict(monster_slug=slugify("Veil Wisp"), material_slug=slugify("Tin Shard"), drop_weight=12),
    dict(monster_slug=slugify("Veil Wisp"), material_slug=slugify("Ember Dust"), drop_weight=8),
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

        for data in RUNE_TEMPLATES:
            if db.query(RuneTemplate).filter_by(slug=data["slug"]).first():
                continue
            db.add(RuneTemplate(**data))

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
            recipe_kwargs = dict(
                slug=data["slug"],
                name=data["name"],
                category=data["category"],
                level_requirement=data["level_requirement"],
                output_quantity=data["output_quantity"],
            )
            if "output_rune_slug" in data:
                output_rune = db.query(RuneTemplate).filter_by(slug=data["output_rune_slug"]).first()
                if output_rune is None:
                    continue
                recipe_kwargs["output_rune_template_id"] = output_rune.id
            else:
                output_consumable = (
                    db.query(ConsumableTemplate).filter_by(slug=data["output_consumable_slug"]).first()
                )
                if output_consumable is None:
                    continue
                recipe_kwargs["output_consumable_template_id"] = output_consumable.id
            recipe = CraftingRecipe(**recipe_kwargs)
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

        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    seed()
