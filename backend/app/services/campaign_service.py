import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.campaign import CampaignNode
from app.models.hero import Hero
from app.models.monster import MonsterTemplate
from app.models.veil_run import VeilRun
from app.services import veil_service
from app.services.combat import encounter as encounter_service


class CampaignError(Exception):
    """Base class for campaign-node entry failures."""


class NodeNotFoundError(CampaignError):
    pass


class NodeLockedError(CampaignError):
    pass


class InsufficientGoldError(CampaignError):
    pass


class ActiveRunConflictError(CampaignError):
    pass


def list_nodes(db: Session) -> list[CampaignNode]:
    return (
        db.execute(
            select(CampaignNode)
            .options(joinedload(CampaignNode.monster_template))
            .order_by(CampaignNode.order_index)
        )
        .scalars()
        .all()
    )


def enter_campaign_node(db: Session, hero: Hero, node_id: uuid.UUID) -> VeilRun:
    """Validates eligibility, charges the node's gold cost, and starts a veil
    run against the node's fixed monster. Combat resolves immediately but
    stays hidden until the run's resolves_at, exactly like a random veil run.
    """
    node = db.get(CampaignNode, node_id)
    if node is None:
        raise NodeNotFoundError(f"campaign node {node_id} not found")

    if veil_service.get_active_run(db, hero) is not None:
        raise ActiveRunConflictError("hero already has an active veil run")

    if node.order_index > hero.campaign_progress + 1:
        raise NodeLockedError("previous campaign node has not been cleared yet")
    if hero.level < node.required_level:
        raise NodeLockedError("hero level is too low for this node")
    if hero.gold < node.gold_cost:
        raise InsufficientGoldError("not enough gold to enter this node")

    monster = db.get(MonsterTemplate, node.monster_template_id)
    if monster is None:
        raise NodeNotFoundError("campaign node's monster template is missing")
    encounter = encounter_service.build_encounter(db, monster)

    hero.gold -= node.gold_cost
    db.add(hero)

    return veil_service.enter_campaign_encounter(db, hero, encounter, node.id)
