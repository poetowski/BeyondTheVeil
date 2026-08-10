import uuid
from typing import Literal

from pydantic import BaseModel

from app.models.campaign import CampaignChapter, CampaignNode
from app.models.hero import Hero

CampaignNodeStatus = Literal["locked", "available", "cleared"]


class CampaignChapterOut(BaseModel):
    id: uuid.UUID
    slug: str
    title: str
    order_index: int


class CampaignNodeOut(BaseModel):
    id: uuid.UUID
    chapter_id: uuid.UUID
    order_index: int
    name: str
    required_level: int
    monster_name: str
    status: CampaignNodeStatus


def to_chapter_out(chapter: CampaignChapter) -> CampaignChapterOut:
    return CampaignChapterOut(
        id=chapter.id,
        slug=chapter.slug,
        title=chapter.title,
        order_index=chapter.order_index,
    )


def to_out(node: CampaignNode, hero: Hero) -> CampaignNodeOut:
    if node.order_index <= hero.campaign_progress:
        status: CampaignNodeStatus = "cleared"
    elif node.order_index == hero.campaign_progress + 1:
        status = "available"
    else:
        status = "locked"

    return CampaignNodeOut(
        id=node.id,
        chapter_id=node.chapter_id,
        order_index=node.order_index,
        name=node.name,
        required_level=node.required_level,
        monster_name=node.monster_template.name,
        status=status,
    )
