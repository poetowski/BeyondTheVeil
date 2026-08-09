from pydantic import BaseModel

from app.models.hero import Hero


class LeaderboardEntryOut(BaseModel):
    rank: int
    name: str
    level: int


def to_out(rank: int, hero: Hero) -> LeaderboardEntryOut:
    return LeaderboardEntryOut(rank=rank, name=hero.name, level=hero.level)
