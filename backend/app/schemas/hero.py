import uuid
from typing import Literal

from pydantic import BaseModel

from app.models.hero import Hero
from app.models.item import ItemInstance
from app.services import hero_service
from app.services.combat.engine import compute_damage_range, compute_spell_damage_range

StatName = Literal["strength", "dexterity", "intelligence", "vitality", "agility", "spirit"]


class StatTrainRequest(BaseModel):
    stat: StatName


class AvatarSelectRequest(BaseModel):
    avatar_slug: str


class HeroOut(BaseModel):
    id: uuid.UUID
    name: str
    avatar_slug: str
    level: int
    xp: int
    xp_to_next_level: int
    gold: int
    inventory_capacity: int
    strength: int
    dexterity: int
    intelligence: int
    vitality: int
    agility: int
    spirit: int
    base_strength: int
    base_dexterity: int
    base_intelligence: int
    base_vitality: int
    base_agility: int
    base_spirit: int
    bonus_strength: int
    bonus_dexterity: int
    bonus_intelligence: int
    bonus_vitality: int
    bonus_agility: int
    bonus_spirit: int
    current_hp: int
    max_hp: int
    damage_min: int
    damage_max: int
    spell_damage_min: int
    spell_damage_max: int
    defense_shield: int
    defense_armor: int
    defense_helmet: int
    train_costs: dict[StatName, int]


def to_out(hero: Hero, equipped_items: list[ItemInstance]) -> HeroOut:
    base = hero_service.compute_base_stats(hero)
    bonus = hero_service.compute_stat_bonuses(hero, equipped_items)
    effective = {stat: base[stat] + bonus[stat] for stat in hero_service.STAT_NAMES}
    bonus_max_hp = hero_service.compute_bonus_max_hp(equipped_items)
    max_hp = hero_service.compute_max_hp(effective["vitality"], bonus_max_hp)
    current_hp = hero_service.compute_current_hp(
        hero, effective["vitality"], bonus_max_hp=bonus_max_hp
    )
    train_costs = {stat: hero_service.train_stat_cost(base[stat]) for stat in hero_service.STAT_NAMES}
    weapon_range = hero_service.compute_weapon_damage_range(equipped_items)
    spell_range = hero_service.compute_spell_damage_range(equipped_items)
    zone_defense = hero_service.compute_zone_defense(equipped_items)
    damage_min, damage_max = compute_damage_range(effective["strength"], weapon_range)
    spell_damage_min, spell_damage_max = compute_spell_damage_range(effective["intelligence"], spell_range)

    return HeroOut(
        id=hero.id,
        name=hero.name,
        avatar_slug=hero.avatar_template.slug,
        level=hero.level,
        xp=hero.xp,
        xp_to_next_level=hero_service.xp_required_for_level(hero.level),
        gold=hero.gold,
        inventory_capacity=hero.inventory_capacity,
        current_hp=current_hp,
        max_hp=max_hp,
        damage_min=damage_min,
        damage_max=damage_max,
        spell_damage_min=spell_damage_min,
        spell_damage_max=spell_damage_max,
        defense_shield=zone_defense["shield"],
        defense_armor=zone_defense["armor"],
        defense_helmet=zone_defense["helmet"],
        train_costs=train_costs,
        **effective,
        **{f"base_{stat}": value for stat, value in base.items()},
        **{f"bonus_{stat}": value for stat, value in bonus.items()},
    )
