import uuid
from typing import Literal

from pydantic import BaseModel

from app.models.campaign import CampaignNode
from app.models.hero import Hero

CampaignNodeStatus = Literal["locked", "available", "cleared"]


class CampaignNodeOut(BaseModel):
    id: uuid.UUID
    order_index: int
    name: str
    required_level: int
    gold_cost: int
    monster_name: str
    status: CampaignNodeStatus


def to_out(node: CampaignNode, hero: Hero) -> CampaignNodeOut:
    if node.order_index <= hero.campaign_progress:
        status: CampaignNodeStatus = "cleared"
    elif node.order_index == hero.campaign_progress + 1:
        status = "available"
    else:
        status = "locked"

    return CampaignNodeOut(
        id=node.id,
        order_index=node.order_index,
        name=node.name,
        required_level=node.required_level,
        gold_cost=node.gold_cost,
        monster_name=node.monster_template.name,
        status=status,
    )
