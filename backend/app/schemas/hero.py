import uuid

from pydantic import BaseModel


class HeroOut(BaseModel):
    id: uuid.UUID
    name: str
    level: int
    xp: int
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
