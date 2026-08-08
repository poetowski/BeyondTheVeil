import uuid
from typing import Literal

from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.models.hero import Hero
from app.services import hero_service


class HeroOut(BaseModel):
    id: uuid.UUID
    name: str
    level: int
    xp: int
    xp_into_level: int
    xp_for_next_level: int
    available_stat_points: int
    gold: int
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
    max_hp: int


class AllocateStatRequest(BaseModel):
    stat: Literal["strength", "dexterity", "intelligence", "vitality", "agility", "spirit"]
    amount: int


def to_out(db: Session, hero: Hero) -> HeroOut:
    equipped_items = hero_service.get_equipped_items(db, hero)
    base = hero_service.compute_base_stats(hero)
    bonus = hero_service.compute_stat_bonuses(hero, equipped_items)
    effective = {stat: base[stat] + bonus[stat] for stat in hero_service.STAT_NAMES}
    max_hp = hero_service.compute_max_hp(effective["vitality"])
    xp_into_level, xp_for_next_level = hero_service.xp_progress(hero)

    return HeroOut(
        id=hero.id,
        name=hero.name,
        level=hero.level,
        xp=hero.xp,
        xp_into_level=xp_into_level,
        xp_for_next_level=xp_for_next_level,
        available_stat_points=hero.available_stat_points,
        gold=hero.gold,
        max_hp=max_hp,
        **effective,
        **{f"base_{stat}": value for stat, value in base.items()},
        **{f"bonus_{stat}": value for stat, value in bonus.items()},
    )
