"""Seed a handful of dev item/monster templates. Content data only, kept out
of Alembic migrations so migrations stay repeatable and diffable.

Run with: python -m scripts.seed_dev_data
"""

import re

from app.core.db import SessionLocal
from app.models.avatar import AvatarTemplate
from app.models.consumable import ConsumableTemplate
from app.models.crafting import CraftingCategory, CraftingRecipe, CraftingRecipeIngredient
from app.models.item import EquipmentSlot, ItemRarity, ItemTemplate
from app.models.material import MaterialTemplate
from app.models.monster import MonsterLootEntry, MonsterMaterialLootEntry, MonsterTemplate
from app.models.rune import RuneTemplate


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


# Peasant Avatar's row is inserted directly by
# alembic/versions/1df83ccc9129_add_avatar_system.py (with a fixed id, since
# every already-existing hero is backfilled to point at it) - it's listed
# here too, insert-if-missing like everything else, purely so a fresh
# install that skips straight to this script still gets it.
AVATAR_TEMPLATES = [
    dict(name="Peasant Avatar", price=0, sort_order=0),
    dict(name="Militia Avatar", price=2000, sort_order=1),
    # Free, but level-gated instead of purchased - unlocks automatically
    # once the hero reaches level 10 (see hero_service.is_avatar_unlocked).
    dict(name="Warrior Avatar", price=0, level_requirement=10, sort_order=2),
]
for _avatar in AVATAR_TEMPLATES:
    _avatar["slug"] = slugify(_avatar["name"])

# Just one worked example per template type (level 1 items, one monster's loot
# table) for the user to extend. Slugs are always derived from `name` via
# slugify() - never hand-typed.
ITEM_TEMPLATES = [
    # Tier1 gear set: defined through the weapon-damage/defense/bonus-HP
    # mechanics instead of flat stat bonuses (base_stats={}).
    dict(name="Wooden Stick", slot=EquipmentSlot.WEAPON, rarity=ItemRarity.COMMON, level_requirement=1, base_stats={}, damage_min=2, damage_max=6, description="Barely a weapon.", price=140),
    dict(name="Wooden Shield", slot=EquipmentSlot.SHIELD, rarity=ItemRarity.COMMON, level_requirement=1, base_stats={}, defense=3, description="Old wood and hide, but it holds.", price=175),
    dict(name="Leather Helm", slot=EquipmentSlot.HELMET, rarity=ItemRarity.COMMON, level_requirement=1, base_stats={}, defense=2, description="Better than nothing.", price=126),
    dict(name="Leather Robe", slot=EquipmentSlot.ARMOR, rarity=ItemRarity.COMMON, level_requirement=1, base_stats={}, defense=1, description="Thin leather, loosely stitched.", price=84),
    dict(name="Old Ring", slot=EquipmentSlot.AMULET, rarity=ItemRarity.COMMON, level_requirement=1, base_stats={}, bonus_max_hp=20, description="Worn smooth by someone else.", price=315),
    # Tier2 "Iron" gear set: same mechanics as tier1, roughly double the
    # stats and ~2.5-3x the price. Spell Skill has no tier2 counterpart yet.
    dict(name="Iron Sword", slot=EquipmentSlot.WEAPON, rarity=ItemRarity.UNCOMMON, level_requirement=4, base_stats={}, damage_min=5, damage_max=12, description="Honest, well-balanced steel.", price=380),
    dict(name="Iron Buckler", slot=EquipmentSlot.SHIELD, rarity=ItemRarity.UNCOMMON, level_requirement=4, base_stats={}, defense=7, description="Small, round, and dented from use.", price=430),
    dict(name="Iron Helm", slot=EquipmentSlot.HELMET, rarity=ItemRarity.UNCOMMON, level_requirement=4, base_stats={}, defense=4, description="A solid cap of hammered iron.", price=320),
    dict(name="Chainmail", slot=EquipmentSlot.ARMOR, rarity=ItemRarity.UNCOMMON, level_requirement=4, base_stats={}, defense=4, description="Interlocked rings, heavy but reliable.", price=260),
    dict(name="Iron Band", slot=EquipmentSlot.AMULET, rarity=ItemRarity.UNCOMMON, level_requirement=4, base_stats={}, bonus_max_hp=55, description="Plain iron, cold against the skin.", price=620),
    # Tier2.5 gear set: level 6, rarity RARE, roughly 20-30% better than
    # tier2's stats/price. Bare names, no shared theme prefix. Spell Skill
    # has no counterpart yet. No amulet here - see the two level-9
    # Talismans below instead.
    dict(name="Mace", slot=EquipmentSlot.WEAPON, rarity=ItemRarity.RARE, level_requirement=6, base_stats={}, damage_min=6, damage_max=15, description="No edge to sharpen - it doesn't need one.", price=480),
    dict(name="Kite Shield", slot=EquipmentSlot.SHIELD, rarity=ItemRarity.RARE, level_requirement=6, base_stats={}, defense=9, description="Long enough to cover the whole leg.", price=540),
    dict(name="Barbute", slot=EquipmentSlot.HELMET, rarity=ItemRarity.RARE, level_requirement=6, base_stats={}, defense=5, description="A T-shaped slit is all it gives you to see by.", price=400),
    dict(name="Brigandine", slot=EquipmentSlot.ARMOR, rarity=ItemRarity.RARE, level_requirement=6, base_stats={}, defense=5, description="Small steel plates riveted under tough cloth.", price=330),
    # Two level-9 amulets with a flat stat bonus (like the runes'
    # stat_bonuses), not bonus_max_hp like Old Ring/Iron Band - replaces
    # a single generic "Talisman" originally proposed for tier2.5.
    dict(name="Spirit Talisman", slot=EquipmentSlot.AMULET, rarity=ItemRarity.RARE, level_requirement=9, base_stats={"spirit": 5}, description="A quiet hum that settles the mind before it settles the hand.", price=850),
    dict(name="Agility Talisman", slot=EquipmentSlot.AMULET, rarity=ItemRarity.RARE, level_requirement=9, base_stats={"agility": 5}, description="Light as a held breath.", price=850),
    # First Spell Skill item - level 10, EPIC, boss-exclusive drop from
    # Mage Adept only (see MONSTER_LOOT_ENTRIES below).
    dict(name="Frozen Spark", slot=EquipmentSlot.SPELL_SKILL, rarity=ItemRarity.EPIC, level_requirement=10, base_stats={}, spell_damage_min=20, spell_damage_max=34, description="A single spark, frozen mid-flight - it still burns going in.", price=1400),
    # Tier3 gear: level 10, EPIC, two lines per slot (weapon/shield/helmet/
    # armor/amulet - no Spell Skill counterpart, Frozen Spark already
    # covers that slot). Adept's line trades some raw damage/defense for a
    # small secondary stat bonus (base_stats, same mechanism the Talismans
    # use); Steel line is pure maximized primary stat, no secondary bonus -
    # a real choice between raw power and build support, not a reskin.
    # Deliberately no MONSTER_LOOT_ENTRIES yet - these are meant to drop
    # from monsters that don't exist yet; for now they're shop-only, same
    # as every ItemTemplate is by default (see shop_service.roll_daily_shop).
    dict(name="Adept's Fang", slot=EquipmentSlot.WEAPON, rarity=ItemRarity.EPIC, level_requirement=10, base_stats={"intelligence": 3}, damage_min=7, damage_max=16, description="It doesn't just cut - it remembers cutting.", price=1250),
    dict(name="Steel Cleaver", slot=EquipmentSlot.WEAPON, rarity=ItemRarity.EPIC, level_requirement=10, base_stats={}, damage_min=9, damage_max=20, description="No trick to it. Just weight, and where you put it.", price=1350),
    dict(name="Adept's Ward", slot=EquipmentSlot.SHIELD, rarity=ItemRarity.EPIC, level_requirement=10, base_stats={"spirit": 3}, defense=10, description="It stops the blow before the blow decides to land.", price=1150),
    dict(name="Steel Bulwark", slot=EquipmentSlot.SHIELD, rarity=ItemRarity.EPIC, level_requirement=10, base_stats={}, defense=13, description="Nothing subtle about it. Nothing gets through it either.", price=1250),
    dict(name="Adept's Circlet", slot=EquipmentSlot.HELMET, rarity=ItemRarity.EPIC, level_requirement=10, base_stats={"intelligence": 3}, defense=6, description="Thin as a promise, and just as binding.", price=950),
    dict(name="Steel Helm", slot=EquipmentSlot.HELMET, rarity=ItemRarity.EPIC, level_requirement=10, base_stats={}, defense=8, description="Dented twice already. Still on somebody's head.", price=1000),
    dict(name="Adept's Scale", slot=EquipmentSlot.ARMOR, rarity=ItemRarity.EPIC, level_requirement=10, base_stats={"agility": 3}, defense=6, description="Each plate shifts before the strike does.", price=950),
    dict(name="Steel Plate", slot=EquipmentSlot.ARMOR, rarity=ItemRarity.EPIC, level_requirement=10, base_stats={}, defense=8, description="Heavier than it looks. Looks heavy.", price=1000),
    dict(name="Adept's Pendant", slot=EquipmentSlot.AMULET, rarity=ItemRarity.EPIC, level_requirement=10, base_stats={"intelligence": 7}, description="A thought, worn close enough to finish it for you.", price=1500),
    dict(name="Steel Signet", slot=EquipmentSlot.AMULET, rarity=ItemRarity.EPIC, level_requirement=10, base_stats={"strength": 4, "dexterity": 4}, description="Plain steel, sized for a fist that's used to closing.", price=1500),
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
    dict(
        name="Light Bandit",
        level_range_min=3,
        level_range_max=5,
        base_stats={"strength": 13, "dexterity": 17, "intelligence": 5, "vitality": 12, "agility": 16, "spirit": 7},
        flavor_text="Barely armored and always moving - it strikes from just outside the reach of your blade, then vanishes before you can answer.",
        no_drop_weight=45,
        no_material_drop_weight=65,
        gold_min=25,
        gold_max=50,
        weapon_attack_min=3,
        weapon_attack_max=6,
        defense=1,
        spell_attack_min=0,
        spell_attack_max=1,
    ),
    dict(
        name="Boar",
        level_range_min=4,
        level_range_max=7,
        base_stats={"strength": 26, "dexterity": 12, "intelligence": 3, "vitality": 28, "agility": 11, "spirit": 8},
        flavor_text="It doesn't charge to scare you off - you're just in its way, and it isn't stopping.",
        no_drop_weight=40,
        no_material_drop_weight=55,
        gold_min=35,
        gold_max=70,
        weapon_attack_min=6,
        weapon_attack_max=10,
        defense=3,
        spell_attack_min=0,
        spell_attack_max=0,
    ),
    dict(
        name="Puny Goblin",
        level_range_min=5,
        level_range_max=7,
        base_stats={"strength": 9, "dexterity": 20, "intelligence": 12, "vitality": 9, "agility": 19, "spirit": 11},
        flavor_text="Barely reaches your knee, and it knows it - so it never fights fair, and it never fights alone for long.",
        no_drop_weight=40,
        no_material_drop_weight=60,
        gold_min=30,
        gold_max=60,
        weapon_attack_min=3,
        weapon_attack_max=6,
        defense=0,
        spell_attack_min=2,
        spell_attack_max=5,
    ),
    dict(
        name="Robber",
        level_range_min=6,
        level_range_max=10,
        base_stats={"strength": 20, "dexterity": 30, "intelligence": 6, "vitality": 22, "agility": 28, "spirit": 10},
        flavor_text="He doesn't want a fight - he wants your bag, and he's faster than you either way.",
        no_drop_weight=35,
        no_material_drop_weight=55,
        gold_min=50,
        gold_max=100,
        weapon_attack_min=8,
        weapon_attack_max=14,
        defense=2,
        spell_attack_min=0,
        spell_attack_max=1,
    ),
    dict(
        name="Dire Wolf",
        level_range_min=6,
        level_range_max=10,
        base_stats={"strength": 34, "dexterity": 18, "intelligence": 4, "vitality": 40, "agility": 16, "spirit": 10},
        flavor_text="Bigger than any wolf has a right to be, and it's already decided you're not getting past it.",
        no_drop_weight=55,
        no_material_drop_weight=50,
        gold_min=55,
        gold_max=110,
        weapon_attack_min=10,
        weapon_attack_max=16,
        defense=4,
        spell_attack_min=0,
        spell_attack_max=0,
    ),
    dict(
        name="Awakened Bear",
        level_range_min=8,
        level_range_max=10,
        base_stats={"strength": 42, "dexterity": 35, "intelligence": 5, "vitality": 50, "agility": 22, "spirit": 12},
        flavor_text="It slept through the cold, and it slept through worse - now it's awake, and everything nearby is a threat.",
        no_drop_weight=40,
        no_material_drop_weight=50,
        gold_min=70,
        gold_max=130,
        weapon_attack_min=12,
        weapon_attack_max=20,
        defense=6,
        spell_attack_min=0,
        spell_attack_max=0,
    ),
    dict(
        name="Mage Adept",
        level_range_min=10,
        level_range_max=12,
        base_stats={"strength": 15, "dexterity": 20, "intelligence": 55, "vitality": 45, "agility": 18, "spirit": 50},
        flavor_text="Robed, bald, and perfectly still - the fire hanging over its palms has been waiting longer than you have.",
        no_drop_weight=20,
        no_material_drop_weight=25,
        gold_min=150,
        gold_max=300,
        weapon_attack_min=7,
        weapon_attack_max=10,
        defense=3,
        spell_attack_min=6,
        spell_attack_max=18,
    ),
    # Level 10-15: the tier just past Mage Adept - also the first content
    # to reach past level 12 at all. Carries tier3 gear + the new
    # materials (see MONSTER_LOOT_ENTRIES/MONSTER_MATERIAL_LOOT_ENTRIES
    # below), weighted differently per monster to match its concept.
    dict(
        name="Bandit",
        level_range_min=10,
        level_range_max=15,
        base_stats={"strength": 40, "dexterity": 55, "intelligence": 8, "vitality": 50, "agility": 48, "spirit": 15},
        flavor_text="He stopped running a long time ago - now you're the one who should.",
        no_drop_weight=60,
        no_material_drop_weight=30,
        gold_min=160,
        gold_max=320,
        weapon_attack_min=10,
        weapon_attack_max=18,
        defense=3,
        spell_attack_min=0,
        spell_attack_max=0,
    ),
    dict(
        name="Broodmother",
        level_range_min=10,
        level_range_max=15,
        base_stats={"strength": 35, "dexterity": 50, "intelligence": 10, "vitality": 55, "agility": 50, "spirit": 15},
        flavor_text="Everything in this hollow that used to move now just feeds her.",
        no_drop_weight=65,
        no_material_drop_weight=25,
        gold_min=90,
        gold_max=180,
        weapon_attack_min=12,
        weapon_attack_max=20,
        defense=5,
        spell_attack_min=0,
        spell_attack_max=4,
    ),
    dict(
        name="Imp",
        level_range_min=10,
        level_range_max=15,
        base_stats={"strength": 15, "dexterity": 35, "intelligence": 60, "vitality": 35, "agility": 45, "spirit": 35},
        flavor_text="It laughs first, then it burns you, then it laughs again.",
        no_drop_weight=60,
        no_material_drop_weight=28,
        gold_min=120,
        gold_max=240,
        weapon_attack_min=6,
        weapon_attack_max=14,
        defense=1,
        spell_attack_min=14,
        spell_attack_max=28,
    ),
]
for _monster in MONSTER_TEMPLATES:
    _monster["slug"] = slugify(_monster["name"])

MATERIAL_TEMPLATES = [
    dict(name="Plantago", description="Broad leaves, bruised for their sap.", category=CraftingCategory.ALCHEMY, price=28, level_requirement=1),
    dict(name="Chamomile", description="Daisy-like flowers, dried for their mild sedative properties.", category=CraftingCategory.ALCHEMY, price=21, level_requirement=1),
    dict(name="Iron Ore", description="Rough-smelted lumps, still warm from the earth.", category=CraftingCategory.FORGE, price=35, level_requirement=1),
    dict(name="Tin Shard", description="Bright, brittle fragments that ring when struck.", category=CraftingCategory.FORGE, price=42, level_requirement=1),
    dict(name="Ember Dust", description="Fine grey ash from a forge fire, still faintly hot.", category=CraftingCategory.FORGE, price=56, level_requirement=1),
    # Level 4 - only drops from level 4+ monsters (Boar, Puny Goblin).
    dict(name="Nettle", description="Fine-toothed leaves that sting on contact, prized once the sting is boiled out.", category=CraftingCategory.ALCHEMY, price=59, level_requirement=4),
    # Level 6 Forge materials - no monster loot table entries or recipe use
    # yet, same as when Nettle was first added; auto-available via the Shop.
    dict(name="Coal", description="Plain black lumps, but no forge burns hot enough without them.", category=CraftingCategory.FORGE, price=85, level_requirement=6),
    dict(name="Scrap Metal", description="Bent, rusted odds and ends - not much to look at, but the furnace doesn't care.", category=CraftingCategory.FORGE, price=90, level_requirement=6),
    dict(name="Veil Crystal", description="A shard of crystallized veil-light, humming faintly even at rest.", category=CraftingCategory.FORGE, price=130, level_requirement=6),
    # Drops from Robber, Dire Wolf, and Awakened Bear - the central
    # ingredient for the two craftable Talisman amulets.
    dict(name="Gem", description="A cut, glinting stone - valuable on its own, prized more for what it can hold.", category=CraftingCategory.FORGE, price=180, level_requirement=6),
    # Level 8 - drops from Robber, Dire Wolf, and Awakened Bear (the three
    # monsters overlapping level 8). Silverleaf is Superior Healing
    # Potion's key ingredient.
    dict(name="Silverleaf", description="Pale, silvery leaves that never quite wilt.", category=CraftingCategory.ALCHEMY, price=140, level_requirement=8),
    dict(name="Ancient Porcelain", description="Fragments of a bowl or urn, glazed white, older than anything else nearby.", category=CraftingCategory.FORGE, price=160, level_requirement=10),
    # No monster loot table entries or recipe use yet, same as when Coal/
    # Scrap Metal/Veil Crystal were first added - auto-available via Shop.
    # Grounded/natural rather than mid-or-endgame exotic, even though the
    # level gate is still 10 - renamed from Starsteel Ingot/Voidglass
    # Shard/Phoenix Ash by alembic/versions/<rename_forge_materials>.py.
    dict(name="Veilbloom", description="A pale flower that only opens where the Veil runs thin.", category=CraftingCategory.ALCHEMY, price=150, level_requirement=10),
    dict(name="Steelhide", description="Hide boiled and pressed until it holds an edge like steel.", category=CraftingCategory.FORGE, price=190, level_requirement=10),
    dict(name="Soul Part", description="A small, cold weight left behind after something stopped being alive.", category=CraftingCategory.FORGE, price=180, level_requirement=10),
    dict(name="Silver Ore", description="Raw ore, veined with silver before anyone's touched it.", category=CraftingCategory.FORGE, price=170, level_requirement=10),
]
for _material in MATERIAL_TEMPLATES:
    _material["slug"] = slugify(_material["name"])

# Naming convention: "<weird invented word> Rune of <effect word>" - the
# effect word stays plain-English (matches the stat it boosts), the prefix
# is a made-up word with no fixed meaning. Follow this for future runes.
RUNE_TEMPLATES = [
    dict(name="Vrelka Rune of Vigor", description="A dull red glyph, warm to the touch.", stat_bonuses={"vitality": 3}, price=1540, level_requirement=1),
    dict(name="Vosk Rune of Might", description="Three azure shards radiating around a glowing core.", stat_bonuses={"strength": 3}, price=1540, level_requirement=1),
    # Level 8, crafted only from the new level-6 Forge materials (Coal,
    # Scrap Metal, Veil Crystal) - see their CRAFTING_RECIPES entries.
    dict(name="Trask Rune of Finesse", description="A narrow silver glyph, precise down to the last line.", stat_bonuses={"dexterity": 5}, price=2400, level_requirement=8),
    dict(name="Mirel Rune of Fleetness", description="A glyph that seems to blur at the edges, never quite still.", stat_bonuses={"agility": 5}, price=2400, level_requirement=8),
    dict(name="Sythe Rune of Cunning", description="A tangled glyph that rewards a closer look with a hidden second pattern.", stat_bonuses={"intelligence": 5}, price=2400, level_requirement=8),
    # Level 10, the last of the six stats to get a rune. Crafted from
    # existing materials only (Veil Crystal) - no new material this time.
    dict(name="Corvun Rune of Serenity", description="A pale glyph that seems to breathe, slow and unhurried.", stat_bonuses={"spirit": 7}, price=3200, level_requirement=10),
    # The only rune that touches all six stats at once, rather than
    # specializing in one - crafted from Ancient Porcelain.
    dict(name="Duskvar Rune of Wholeness", description="A hairline glyph, fired into old porcelain long before it cracked.", stat_bonuses={"strength": 1, "dexterity": 1, "intelligence": 1, "vitality": 1, "agility": 1, "spirit": 1}, price=4000, level_requirement=10),
    # Level 13, crafted only from the level-10 Forge materials (Steelhide,
    # Soul Part, Silver Ore) in combination - see their CRAFTING_RECIPES
    # entries. Two dual-stat runes plus two pure single-stat runes.
    dict(name="Krevas Rune of Alacrity", description="A glyph split in two - one half precise and still, the other already moving.", stat_bonuses={"dexterity": 5, "agility": 5}, price=5400, level_requirement=13),
    dict(name="Solmira Rune of Insight", description="A cold violet mark fused to a pale, breathing one - thought and stillness, sharing one glyph.", stat_bonuses={"intelligence": 5, "spirit": 5}, price=5400, level_requirement=13),
    dict(name="Dravek Rune of Vigor", description="A dense, leathery glyph that pulses slow and steady, like a second heartbeat.", stat_bonuses={"vitality": 9}, price=4800, level_requirement=13),
    dict(name="Ashgrim Rune of Might", description="A rough-forged glyph, heavier than it looks, veined with ore and old iron.", stat_bonuses={"strength": 9}, price=4800, level_requirement=13),
    # Level 14, a stronger successor to Duskvar's all-six spread - crafted
    # from a heavier load of Ancient Porcelain alone.
    dict(name="Aurelun Rune of Totality", description="A blazing yellow glyph, a red star burning at its center - impossible to look away from.", stat_bonuses={"strength": 2, "dexterity": 2, "intelligence": 2, "vitality": 2, "agility": 2, "spirit": 2}, price=7200, level_requirement=14),
]
for _rune in RUNE_TEMPLATES:
    _rune["slug"] = slugify(_rune["name"])

CONSUMABLE_TEMPLATES = [
    dict(
        name="Minor Healing Potion",
        description="A cloudy brew of crushed herbs, drunk quickly before it settles.",
        heal_flat=100,
        heal_vitality_multiplier=2,
        price=210,
        level_requirement=1,
    ),
    dict(
        name="Greater Healing Potion",
        description="A denser, syrupy brew that hits far harder than its minor cousin - worth the sting to make.",
        heal_flat=220,
        heal_vitality_multiplier=4,
        price=480,
        level_requirement=5,
    ),
    dict(
        name="Superior Healing Potion",
        description="Silverleaf steeped until the water turns bright as mercury - the strongest brew there is.",
        heal_flat=380,
        heal_vitality_multiplier=6,
        price=850,
        level_requirement=10,
    ),
    dict(
        name="Health Elixir",
        description="Veilbloom petals dissolved until the draught glows faintly - it doesn't just close wounds, it seems to remember how the body was supposed to look.",
        heal_flat=450,
        heal_vitality_multiplier=7,
        price=950,
        level_requirement=15,
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
        name="Greater Healing Potion (Nettle Blend)",
        category=CraftingCategory.ALCHEMY,
        level_requirement=5,
        output_consumable_slug=slugify("Greater Healing Potion"),
        output_quantity=1,
        ingredients=[
            dict(material_slug=slugify("Nettle"), quantity_required=3),
            dict(material_slug=slugify("Plantago"), quantity_required=2),
            dict(material_slug=slugify("Chamomile"), quantity_required=2),
        ],
    ),
    dict(
        name="Greater Healing Potion (Nettle Concentrate)",
        category=CraftingCategory.ALCHEMY,
        level_requirement=5,
        output_consumable_slug=slugify("Greater Healing Potion"),
        output_quantity=1,
        ingredients=[dict(material_slug=slugify("Nettle"), quantity_required=6)],
    ),
    dict(
        name="Superior Healing Potion (Silverleaf Brew)",
        category=CraftingCategory.ALCHEMY,
        level_requirement=10,
        output_consumable_slug=slugify("Superior Healing Potion"),
        output_quantity=1,
        ingredients=[dict(material_slug=slugify("Silverleaf"), quantity_required=6)],
    ),
    dict(
        name="Health Elixir (Veilbloom Blend)",
        category=CraftingCategory.ALCHEMY,
        level_requirement=15,
        output_consumable_slug=slugify("Health Elixir"),
        output_quantity=1,
        ingredients=[dict(material_slug=slugify("Veilbloom"), quantity_required=5)],
    ),
    dict(
        name="Vrelka Rune of Vigor",
        category=CraftingCategory.FORGE,
        level_requirement=1,
        output_rune_slug=slugify("Vrelka Rune of Vigor"),
        output_quantity=1,
        ingredients=[
            dict(material_slug=slugify("Iron Ore"), quantity_required=3),
            dict(material_slug=slugify("Ember Dust"), quantity_required=2),
        ],
    ),
    dict(
        name="Vosk Rune of Might",
        category=CraftingCategory.FORGE,
        level_requirement=1,
        output_rune_slug=slugify("Vosk Rune of Might"),
        output_quantity=1,
        ingredients=[
            dict(material_slug=slugify("Tin Shard"), quantity_required=3),
            dict(material_slug=slugify("Ember Dust"), quantity_required=2),
        ],
    ),
    dict(
        name="Trask Rune of Finesse",
        category=CraftingCategory.FORGE,
        level_requirement=8,
        output_rune_slug=slugify("Trask Rune of Finesse"),
        output_quantity=1,
        ingredients=[
            dict(material_slug=slugify("Scrap Metal"), quantity_required=4),
            dict(material_slug=slugify("Veil Crystal"), quantity_required=2),
        ],
    ),
    dict(
        name="Mirel Rune of Fleetness",
        category=CraftingCategory.FORGE,
        level_requirement=8,
        output_rune_slug=slugify("Mirel Rune of Fleetness"),
        output_quantity=1,
        ingredients=[
            dict(material_slug=slugify("Coal"), quantity_required=4),
            dict(material_slug=slugify("Veil Crystal"), quantity_required=2),
        ],
    ),
    dict(
        name="Sythe Rune of Cunning",
        category=CraftingCategory.FORGE,
        level_requirement=8,
        output_rune_slug=slugify("Sythe Rune of Cunning"),
        output_quantity=1,
        ingredients=[
            dict(material_slug=slugify("Coal"), quantity_required=2),
            dict(material_slug=slugify("Scrap Metal"), quantity_required=2),
            dict(material_slug=slugify("Veil Crystal"), quantity_required=3),
        ],
    ),
    dict(
        name="Corvun Rune of Serenity",
        category=CraftingCategory.FORGE,
        level_requirement=10,
        output_rune_slug=slugify("Corvun Rune of Serenity"),
        output_quantity=1,
        ingredients=[
            dict(material_slug=slugify("Veil Crystal"), quantity_required=9),
        ],
    ),
    dict(
        name="Duskvar Rune of Wholeness",
        category=CraftingCategory.FORGE,
        level_requirement=10,
        output_rune_slug=slugify("Duskvar Rune of Wholeness"),
        output_quantity=1,
        ingredients=[
            dict(material_slug=slugify("Ancient Porcelain"), quantity_required=8),
        ],
    ),
    dict(
        name="Krevas Rune of Alacrity",
        category=CraftingCategory.FORGE,
        level_requirement=13,
        output_rune_slug=slugify("Krevas Rune of Alacrity"),
        output_quantity=1,
        ingredients=[
            dict(material_slug=slugify("Silver Ore"), quantity_required=5),
            dict(material_slug=slugify("Steelhide"), quantity_required=4),
        ],
    ),
    dict(
        name="Solmira Rune of Insight",
        category=CraftingCategory.FORGE,
        level_requirement=13,
        output_rune_slug=slugify("Solmira Rune of Insight"),
        output_quantity=1,
        ingredients=[
            dict(material_slug=slugify("Soul Part"), quantity_required=5),
            dict(material_slug=slugify("Silver Ore"), quantity_required=4),
        ],
    ),
    dict(
        name="Dravek Rune of Vigor",
        category=CraftingCategory.FORGE,
        level_requirement=13,
        output_rune_slug=slugify("Dravek Rune of Vigor"),
        output_quantity=1,
        ingredients=[
            dict(material_slug=slugify("Steelhide"), quantity_required=5),
            dict(material_slug=slugify("Soul Part"), quantity_required=4),
        ],
    ),
    dict(
        name="Ashgrim Rune of Might",
        category=CraftingCategory.FORGE,
        level_requirement=13,
        output_rune_slug=slugify("Ashgrim Rune of Might"),
        output_quantity=1,
        ingredients=[
            dict(material_slug=slugify("Steelhide"), quantity_required=3),
            dict(material_slug=slugify("Soul Part"), quantity_required=3),
            dict(material_slug=slugify("Silver Ore"), quantity_required=3),
        ],
    ),
    dict(
        name="Aurelun Rune of Totality",
        category=CraftingCategory.FORGE,
        level_requirement=14,
        output_rune_slug=slugify("Aurelun Rune of Totality"),
        output_quantity=1,
        ingredients=[
            dict(material_slug=slugify("Ancient Porcelain"), quantity_required=12),
        ],
    ),
    dict(
        name="Spirit Talisman",
        category=CraftingCategory.FORGE,
        level_requirement=9,
        output_item_slug=slugify("Spirit Talisman"),
        output_quantity=1,
        ingredients=[
            dict(material_slug=slugify("Gem"), quantity_required=9),
        ],
    ),
    dict(
        name="Agility Talisman",
        category=CraftingCategory.FORGE,
        level_requirement=9,
        output_item_slug=slugify("Agility Talisman"),
        output_quantity=1,
        ingredients=[
            dict(material_slug=slugify("Gem"), quantity_required=9),
        ],
    ),
]
for _recipe in CRAFTING_RECIPES:
    _recipe["slug"] = slugify(_recipe["name"])

# Young Wolf: each item weight 3 (sum 15), no_drop_weight 45 -> 75% nothing,
# 5% each item.
# Light Bandit reuses the same 5 tier-1 items (its "stolen goods") at the
# same weight-3-each pattern.
# Monsters with level_range_min >= 4 (Boar, Puny Goblin) drop both the
# tier-1 and tier-2 "Iron" item pools - tier-2 weighted 2x a tier-1 item
# (weight 6 vs 3) so better gear is more common, not rarer, at this tier.
MONSTER_LOOT_ENTRIES = [
    dict(monster_slug=slugify("Young Wolf"), item_slug=slugify("Leather Helm"), drop_weight=3),
    dict(monster_slug=slugify("Young Wolf"), item_slug=slugify("Leather Robe"), drop_weight=3),
    dict(monster_slug=slugify("Young Wolf"), item_slug=slugify("Wooden Shield"), drop_weight=3),
    dict(monster_slug=slugify("Young Wolf"), item_slug=slugify("Wooden Stick"), drop_weight=3),
    dict(monster_slug=slugify("Young Wolf"), item_slug=slugify("Old Ring"), drop_weight=3),
    dict(monster_slug=slugify("Light Bandit"), item_slug=slugify("Leather Helm"), drop_weight=3),
    dict(monster_slug=slugify("Light Bandit"), item_slug=slugify("Leather Robe"), drop_weight=3),
    dict(monster_slug=slugify("Light Bandit"), item_slug=slugify("Wooden Shield"), drop_weight=3),
    dict(monster_slug=slugify("Light Bandit"), item_slug=slugify("Wooden Stick"), drop_weight=3),
    dict(monster_slug=slugify("Light Bandit"), item_slug=slugify("Old Ring"), drop_weight=3),
    dict(monster_slug=slugify("Puny Goblin"), item_slug=slugify("Leather Helm"), drop_weight=3),
    dict(monster_slug=slugify("Puny Goblin"), item_slug=slugify("Leather Robe"), drop_weight=3),
    dict(monster_slug=slugify("Puny Goblin"), item_slug=slugify("Wooden Shield"), drop_weight=3),
    dict(monster_slug=slugify("Puny Goblin"), item_slug=slugify("Wooden Stick"), drop_weight=3),
    dict(monster_slug=slugify("Puny Goblin"), item_slug=slugify("Old Ring"), drop_weight=3),
    dict(monster_slug=slugify("Puny Goblin"), item_slug=slugify("Iron Helm"), drop_weight=6),
    dict(monster_slug=slugify("Puny Goblin"), item_slug=slugify("Chainmail"), drop_weight=6),
    dict(monster_slug=slugify("Puny Goblin"), item_slug=slugify("Iron Buckler"), drop_weight=6),
    dict(monster_slug=slugify("Puny Goblin"), item_slug=slugify("Iron Sword"), drop_weight=6),
    dict(monster_slug=slugify("Puny Goblin"), item_slug=slugify("Iron Band"), drop_weight=6),
    dict(monster_slug=slugify("Boar"), item_slug=slugify("Leather Helm"), drop_weight=3),
    dict(monster_slug=slugify("Boar"), item_slug=slugify("Leather Robe"), drop_weight=3),
    dict(monster_slug=slugify("Boar"), item_slug=slugify("Wooden Shield"), drop_weight=3),
    dict(monster_slug=slugify("Boar"), item_slug=slugify("Wooden Stick"), drop_weight=3),
    dict(monster_slug=slugify("Boar"), item_slug=slugify("Old Ring"), drop_weight=3),
    dict(monster_slug=slugify("Boar"), item_slug=slugify("Iron Helm"), drop_weight=6),
    dict(monster_slug=slugify("Boar"), item_slug=slugify("Chainmail"), drop_weight=6),
    dict(monster_slug=slugify("Boar"), item_slug=slugify("Iron Buckler"), drop_weight=6),
    dict(monster_slug=slugify("Boar"), item_slug=slugify("Iron Sword"), drop_weight=6),
    dict(monster_slug=slugify("Boar"), item_slug=slugify("Iron Band"), drop_weight=6),
    # Robber and Dire Wolf (level 6-10) drop tier-2 "Iron" gear at weight 4
    # and tier2.5 gear at weight 8 (better tier = more prevalence, same
    # convention as tier1-vs-tier2 elsewhere) - no Talismans though, those
    # stay Awakened Bear/Forge-only.
    dict(monster_slug=slugify("Robber"), item_slug=slugify("Iron Sword"), drop_weight=4),
    dict(monster_slug=slugify("Robber"), item_slug=slugify("Iron Helm"), drop_weight=4),
    dict(monster_slug=slugify("Robber"), item_slug=slugify("Iron Buckler"), drop_weight=4),
    dict(monster_slug=slugify("Robber"), item_slug=slugify("Chainmail"), drop_weight=4),
    dict(monster_slug=slugify("Robber"), item_slug=slugify("Iron Band"), drop_weight=4),
    dict(monster_slug=slugify("Robber"), item_slug=slugify("Mace"), drop_weight=8),
    dict(monster_slug=slugify("Robber"), item_slug=slugify("Barbute"), drop_weight=8),
    dict(monster_slug=slugify("Robber"), item_slug=slugify("Kite Shield"), drop_weight=8),
    dict(monster_slug=slugify("Robber"), item_slug=slugify("Brigandine"), drop_weight=8),
    dict(monster_slug=slugify("Dire Wolf"), item_slug=slugify("Iron Sword"), drop_weight=4),
    dict(monster_slug=slugify("Dire Wolf"), item_slug=slugify("Iron Helm"), drop_weight=4),
    dict(monster_slug=slugify("Dire Wolf"), item_slug=slugify("Iron Buckler"), drop_weight=4),
    dict(monster_slug=slugify("Dire Wolf"), item_slug=slugify("Chainmail"), drop_weight=4),
    dict(monster_slug=slugify("Dire Wolf"), item_slug=slugify("Iron Band"), drop_weight=4),
    dict(monster_slug=slugify("Dire Wolf"), item_slug=slugify("Mace"), drop_weight=8),
    dict(monster_slug=slugify("Dire Wolf"), item_slug=slugify("Barbute"), drop_weight=8),
    dict(monster_slug=slugify("Dire Wolf"), item_slug=slugify("Kite Shield"), drop_weight=8),
    dict(monster_slug=slugify("Dire Wolf"), item_slug=slugify("Brigandine"), drop_weight=8),
    # Awakened Bear (level 8-10) previously had no item loot table at all -
    # it now drops only tier2.5 gear, including both Talismans at a small
    # weight (2, vs 8 for the other four) so they stay rare.
    dict(monster_slug=slugify("Awakened Bear"), item_slug=slugify("Mace"), drop_weight=8),
    dict(monster_slug=slugify("Awakened Bear"), item_slug=slugify("Barbute"), drop_weight=8),
    dict(monster_slug=slugify("Awakened Bear"), item_slug=slugify("Kite Shield"), drop_weight=8),
    dict(monster_slug=slugify("Awakened Bear"), item_slug=slugify("Brigandine"), drop_weight=8),
    dict(monster_slug=slugify("Awakened Bear"), item_slug=slugify("Spirit Talisman"), drop_weight=2),
    dict(monster_slug=slugify("Awakened Bear"), item_slug=slugify("Agility Talisman"), drop_weight=2),
    # Mage Adept (level 10-12, boss of the 1-10 range) drops the same
    # tier2.5 set, plus both Talismans at a more generous weight (4, vs
    # Awakened Bear's rare weight-2) befitting a boss encounter.
    dict(monster_slug=slugify("Mage Adept"), item_slug=slugify("Mace"), drop_weight=8),
    dict(monster_slug=slugify("Mage Adept"), item_slug=slugify("Barbute"), drop_weight=8),
    dict(monster_slug=slugify("Mage Adept"), item_slug=slugify("Kite Shield"), drop_weight=8),
    dict(monster_slug=slugify("Mage Adept"), item_slug=slugify("Brigandine"), drop_weight=8),
    dict(monster_slug=slugify("Mage Adept"), item_slug=slugify("Spirit Talisman"), drop_weight=4),
    dict(monster_slug=slugify("Mage Adept"), item_slug=slugify("Agility Talisman"), drop_weight=4),
    # Frozen Spark is exclusive to Mage Adept - no other monster's loot table.
    dict(monster_slug=slugify("Mage Adept"), item_slug=slugify("Frozen Spark"), drop_weight=3),
    # Bandit, Broodmother, and Imp (level 10-15) all carry the full tier3
    # set, weighted per-monster to match concept: Bandit favors mundane
    # Steel gear (practical, looted from past victims), Imp favors the
    # arcane Adept's line, Broodmother is roughly even (both lines just
    # read as "things dragged into the lair").
    dict(monster_slug=slugify("Bandit"), item_slug=slugify("Steel Cleaver"), drop_weight=6),
    dict(monster_slug=slugify("Bandit"), item_slug=slugify("Steel Bulwark"), drop_weight=6),
    dict(monster_slug=slugify("Bandit"), item_slug=slugify("Steel Helm"), drop_weight=6),
    dict(monster_slug=slugify("Bandit"), item_slug=slugify("Steel Plate"), drop_weight=6),
    dict(monster_slug=slugify("Bandit"), item_slug=slugify("Steel Signet"), drop_weight=6),
    dict(monster_slug=slugify("Bandit"), item_slug=slugify("Adept's Fang"), drop_weight=3),
    dict(monster_slug=slugify("Bandit"), item_slug=slugify("Adept's Ward"), drop_weight=3),
    dict(monster_slug=slugify("Bandit"), item_slug=slugify("Adept's Circlet"), drop_weight=3),
    dict(monster_slug=slugify("Bandit"), item_slug=slugify("Adept's Scale"), drop_weight=3),
    dict(monster_slug=slugify("Bandit"), item_slug=slugify("Adept's Pendant"), drop_weight=3),

    dict(monster_slug=slugify("Broodmother"), item_slug=slugify("Adept's Fang"), drop_weight=4),
    dict(monster_slug=slugify("Broodmother"), item_slug=slugify("Adept's Ward"), drop_weight=4),
    dict(monster_slug=slugify("Broodmother"), item_slug=slugify("Adept's Circlet"), drop_weight=4),
    dict(monster_slug=slugify("Broodmother"), item_slug=slugify("Adept's Scale"), drop_weight=4),
    dict(monster_slug=slugify("Broodmother"), item_slug=slugify("Adept's Pendant"), drop_weight=4),
    dict(monster_slug=slugify("Broodmother"), item_slug=slugify("Steel Cleaver"), drop_weight=4),
    dict(monster_slug=slugify("Broodmother"), item_slug=slugify("Steel Bulwark"), drop_weight=4),
    dict(monster_slug=slugify("Broodmother"), item_slug=slugify("Steel Helm"), drop_weight=4),
    dict(monster_slug=slugify("Broodmother"), item_slug=slugify("Steel Plate"), drop_weight=4),
    dict(monster_slug=slugify("Broodmother"), item_slug=slugify("Steel Signet"), drop_weight=4),

    dict(monster_slug=slugify("Imp"), item_slug=slugify("Adept's Fang"), drop_weight=6),
    dict(monster_slug=slugify("Imp"), item_slug=slugify("Adept's Ward"), drop_weight=6),
    dict(monster_slug=slugify("Imp"), item_slug=slugify("Adept's Circlet"), drop_weight=6),
    dict(monster_slug=slugify("Imp"), item_slug=slugify("Adept's Scale"), drop_weight=6),
    dict(monster_slug=slugify("Imp"), item_slug=slugify("Adept's Pendant"), drop_weight=6),
    dict(monster_slug=slugify("Imp"), item_slug=slugify("Steel Cleaver"), drop_weight=3),
    dict(monster_slug=slugify("Imp"), item_slug=slugify("Steel Bulwark"), drop_weight=3),
    dict(monster_slug=slugify("Imp"), item_slug=slugify("Steel Helm"), drop_weight=3),
    dict(monster_slug=slugify("Imp"), item_slug=slugify("Steel Plate"), drop_weight=3),
    dict(monster_slug=slugify("Imp"), item_slug=slugify("Steel Signet"), drop_weight=3),
]

# Young Wolf: no_material_drop_weight 70, Chamomile 20, Plantago 10 -> 70%
# nothing, 20% Chamomile, 10% Plantago.
# Veil Wisp: no_material_drop_weight 30, Chamomile 45, Plantago 25 -> 30%
# nothing, 45% Chamomile, 25% Plantago (higher than Young Wolf's since Veil
# Wisp has no item loot table at all).
# Forge materials (Iron Ore, Tin Shard, Ember Dust) are added to all three
# monsters' tables - without a drop source Forge recipes would be craftable
# in name only. Veil Wisp's Ember Dust is weighted well above its other
# Forge drops (33 vs 15/12) to make it the wisp's signature material.
# Light Bandit: no_material_drop_weight 65, Tin Shard weighted highest (18)
# as its signature material ("bright, brittle fragments" fit stolen trinkets).
# Boar: no_material_drop_weight 55, Iron Ore weighted highest (22)
# as its signature material (a beast rooting through rocky ground). Unlike
# Veil Wisp, it now has an item loot table too (see MONSTER_LOOT_ENTRIES) -
# gear trampled off a fallen adventurer, not gear it carries itself.
# Puny Goblin: no_material_drop_weight 60, Plantago weighted highest (20)
# as its signature material (an undergrowth-dweller; no other monster
# favors Plantago).
# Nettle only drops from monsters whose level_range_min is at least 4
# (Boar, Puny Goblin) - it's a tougher-terrain plant, absent from the
# tier-1/2 monsters' tables.
# Awakened Bear: no_material_drop_weight 50, Coal weighted highest (20)
# as its signature material (claws blackened from a scorched den). No item
# loot table - a pure beast, matching Young Wolf/Veil Wisp's original
# precedent (not every beast needs to drop gear).
# Robber and Dire Wolf (level 6-10) are the first drop source for the
# level-6 Forge materials (Coal, Scrap Metal, Veil Crystal), which were
# previously Shop-only. Robber: no_material_drop_weight 55, Scrap Metal
# weighted highest (20) as its signature material (a bandit's scavenged
# loot). Dire Wolf: no_material_drop_weight 50, Veil Crystal weighted
# highest (18) as its signature material (a beast prowling veil-corrupted
# ground). Gem drops from all three of Robber/Dire Wolf/Awakened Bear at
# a shared weight of 12 - the central ingredient for the two craftable
# Talisman amulets. Silverleaf (level 8, Superior Healing Potion's
# ingredient) drops from all three (Robber/Dire Wolf at weight 10 each,
# Awakened Bear at weight 18). Ancient Porcelain (level 10) drops from
# Robber and Awakened Bear only, not Dire Wolf, at the same weights.
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
    dict(monster_slug=slugify("Veil Wisp"), material_slug=slugify("Ember Dust"), drop_weight=33),
    dict(monster_slug=slugify("Light Bandit"), material_slug=slugify("Chamomile"), drop_weight=15),
    dict(monster_slug=slugify("Light Bandit"), material_slug=slugify("Plantago"), drop_weight=8),
    dict(monster_slug=slugify("Light Bandit"), material_slug=slugify("Iron Ore"), drop_weight=10),
    dict(monster_slug=slugify("Light Bandit"), material_slug=slugify("Tin Shard"), drop_weight=18),
    dict(monster_slug=slugify("Light Bandit"), material_slug=slugify("Ember Dust"), drop_weight=8),
    dict(monster_slug=slugify("Boar"), material_slug=slugify("Iron Ore"), drop_weight=22),
    dict(monster_slug=slugify("Boar"), material_slug=slugify("Chamomile"), drop_weight=10),
    dict(monster_slug=slugify("Boar"), material_slug=slugify("Plantago"), drop_weight=8),
    dict(monster_slug=slugify("Boar"), material_slug=slugify("Tin Shard"), drop_weight=10),
    dict(monster_slug=slugify("Boar"), material_slug=slugify("Ember Dust"), drop_weight=6),
    dict(monster_slug=slugify("Boar"), material_slug=slugify("Nettle"), drop_weight=8),
    dict(monster_slug=slugify("Puny Goblin"), material_slug=slugify("Plantago"), drop_weight=20),
    dict(monster_slug=slugify("Puny Goblin"), material_slug=slugify("Chamomile"), drop_weight=12),
    dict(monster_slug=slugify("Puny Goblin"), material_slug=slugify("Iron Ore"), drop_weight=8),
    dict(monster_slug=slugify("Puny Goblin"), material_slug=slugify("Tin Shard"), drop_weight=10),
    dict(monster_slug=slugify("Puny Goblin"), material_slug=slugify("Ember Dust"), drop_weight=6),
    dict(monster_slug=slugify("Puny Goblin"), material_slug=slugify("Nettle"), drop_weight=10),
    dict(monster_slug=slugify("Robber"), material_slug=slugify("Nettle"), drop_weight=10),
    dict(monster_slug=slugify("Robber"), material_slug=slugify("Coal"), drop_weight=10),
    dict(monster_slug=slugify("Robber"), material_slug=slugify("Scrap Metal"), drop_weight=20),
    dict(monster_slug=slugify("Robber"), material_slug=slugify("Veil Crystal"), drop_weight=8),
    dict(monster_slug=slugify("Robber"), material_slug=slugify("Gem"), drop_weight=12),
    dict(monster_slug=slugify("Robber"), material_slug=slugify("Silverleaf"), drop_weight=10),
    dict(monster_slug=slugify("Robber"), material_slug=slugify("Ancient Porcelain"), drop_weight=10),
    dict(monster_slug=slugify("Dire Wolf"), material_slug=slugify("Nettle"), drop_weight=10),
    dict(monster_slug=slugify("Dire Wolf"), material_slug=slugify("Coal"), drop_weight=8),
    dict(monster_slug=slugify("Dire Wolf"), material_slug=slugify("Scrap Metal"), drop_weight=8),
    dict(monster_slug=slugify("Dire Wolf"), material_slug=slugify("Veil Crystal"), drop_weight=18),
    dict(monster_slug=slugify("Dire Wolf"), material_slug=slugify("Gem"), drop_weight=12),
    dict(monster_slug=slugify("Dire Wolf"), material_slug=slugify("Silverleaf"), drop_weight=10),
    dict(monster_slug=slugify("Awakened Bear"), material_slug=slugify("Nettle"), drop_weight=12),
    dict(monster_slug=slugify("Awakened Bear"), material_slug=slugify("Coal"), drop_weight=20),
    dict(monster_slug=slugify("Awakened Bear"), material_slug=slugify("Scrap Metal"), drop_weight=10),
    dict(monster_slug=slugify("Awakened Bear"), material_slug=slugify("Veil Crystal"), drop_weight=10),
    dict(monster_slug=slugify("Awakened Bear"), material_slug=slugify("Gem"), drop_weight=12),
    dict(monster_slug=slugify("Awakened Bear"), material_slug=slugify("Silverleaf"), drop_weight=18),
    dict(monster_slug=slugify("Awakened Bear"), material_slug=slugify("Ancient Porcelain"), drop_weight=18),
    # Mage Adept (level 10-12, boss): Gem and Silverleaf at 15 each, Ancient
    # Porcelain at a big weight (30) as requested.
    dict(monster_slug=slugify("Mage Adept"), material_slug=slugify("Gem"), drop_weight=15),
    dict(monster_slug=slugify("Mage Adept"), material_slug=slugify("Silverleaf"), drop_weight=15),
    dict(monster_slug=slugify("Mage Adept"), material_slug=slugify("Ancient Porcelain"), drop_weight=30),
    # Bandit, Broodmother, and Imp (level 10-15) - all 4 new materials plus
    # Ancient Porcelain, weighted per-monster to match concept.
    dict(monster_slug=slugify("Bandit"), material_slug=slugify("Silver Ore"), drop_weight=20),
    dict(monster_slug=slugify("Bandit"), material_slug=slugify("Ancient Porcelain"), drop_weight=15),
    dict(monster_slug=slugify("Bandit"), material_slug=slugify("Steelhide"), drop_weight=10),
    dict(monster_slug=slugify("Bandit"), material_slug=slugify("Soul Part"), drop_weight=5),
    dict(monster_slug=slugify("Bandit"), material_slug=slugify("Veilbloom"), drop_weight=5),

    dict(monster_slug=slugify("Broodmother"), material_slug=slugify("Steelhide"), drop_weight=20),
    dict(monster_slug=slugify("Broodmother"), material_slug=slugify("Soul Part"), drop_weight=15),
    dict(monster_slug=slugify("Broodmother"), material_slug=slugify("Veilbloom"), drop_weight=12),
    dict(monster_slug=slugify("Broodmother"), material_slug=slugify("Ancient Porcelain"), drop_weight=8),
    dict(monster_slug=slugify("Broodmother"), material_slug=slugify("Silver Ore"), drop_weight=5),

    dict(monster_slug=slugify("Imp"), material_slug=slugify("Soul Part"), drop_weight=20),
    dict(monster_slug=slugify("Imp"), material_slug=slugify("Veilbloom"), drop_weight=15),
    dict(monster_slug=slugify("Imp"), material_slug=slugify("Ancient Porcelain"), drop_weight=12),
    dict(monster_slug=slugify("Imp"), material_slug=slugify("Steelhide"), drop_weight=5),
    dict(monster_slug=slugify("Imp"), material_slug=slugify("Silver Ore"), drop_weight=5),
]


def seed() -> None:
    db = SessionLocal()
    try:
        for data in AVATAR_TEMPLATES:
            if db.query(AvatarTemplate).filter_by(slug=data["slug"]).first():
                continue
            db.add(AvatarTemplate(**data))

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
            if "output_item_slug" in data:
                output_item = db.query(ItemTemplate).filter_by(slug=data["output_item_slug"]).first()
                if output_item is None:
                    continue
                recipe_kwargs["output_item_template_id"] = output_item.id
            elif "output_rune_slug" in data:
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
