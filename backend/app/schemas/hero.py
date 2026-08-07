import uuid

from pydantic import BaseModel


class HeroOut(BaseModel):
    id: uuid.UUID
    name: str
    level: int
    xp: int
    strength: int
    dexterity: int
    vitality: int
    agility: int
    intelligence: int
    spirit: int
    max_hp: int
