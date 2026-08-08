import dataclasses
import random
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.campaign import CampaignNode
from app.models.hero import Hero
from app.models.item import ItemInstance, ItemTemplate
from app.models.veil_run import VeilRun, VeilRunStatus
from app.services import hero_service
from app.services.combat import encounter as encounter_service
from app.services.combat import engine as combat_engine


def enter_veil(db: Session, hero: Hero) -> VeilRun:
    """Start a veil run against a randomly selected monster, resolving combat
    immediately but revealing nothing until `resolves_at` has passed (see
    schemas.veil_run.is_visible).

    Safe under a double-submit: the partial unique index on
    veil_runs(hero_id) WHERE status='in_progress' is the actual guarantee;
    the pre-check here just avoids doing wasted work in the common case.
    """
    existing = get_active_run(db, hero)
    if existing is not None:
        return existing

    seed = random.getrandbits(63)
    encounter = encounter_service.select_encounter(db, hero, seed)
    return _start_run(db, hero, seed=seed, encounter=encounter, campaign_node_id=None)


def enter_campaign_encounter(
    db: Session, hero: Hero, encounter: dict[str, Any], campaign_node_id: uuid.UUID
) -> VeilRun:
    """Starts a run against a fixed (already-resolved) campaign-node monster.

    Mirrors enter_veil's immediate-resolve-but-hidden behavior; the caller
    (campaign_service) is responsible for eligibility checks and gold
    deduction before calling this.
    """
    existing = get_active_run(db, hero)
    if existing is not None:
        return existing

    seed = random.getrandbits(63)
    return _start_run(db, hero, seed=seed, encounter=encounter, campaign_node_id=campaign_node_id)


def _start_run(
    db: Session,
    hero: Hero,
    *,
    seed: int,
    encounter: dict[str, Any] | None,
    campaign_node_id: uuid.UUID | None,
) -> VeilRun:
    equipped_items = hero_service.get_equipped_items(db, hero)
    effective_stats = hero_service.compute_effective_stats(hero, equipped_items)
    base_stats = hero_service.compute_base_stats(hero)

    started_at = datetime.now(timezone.utc)
    duration_seconds = settings.veil_duration_seconds
    resolves_at = started_at + timedelta(seconds=duration_seconds)

    result = combat_engine.resolve(
        seed=seed, hero_snapshot=effective_stats, hero_base_stats=base_stats, encounter=encounter
    )

    run = VeilRun(
        hero_id=hero.id,
        campaign_node_id=campaign_node_id,
        seed=seed,
        status=VeilRunStatus.IN_PROGRESS,
        started_at=started_at,
        duration_seconds=duration_seconds,
        resolves_at=resolves_at,
        result_payload=dataclasses.asdict(result),
    )
    db.add(run)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = get_active_run(db, hero)
        if existing is not None:
            return existing
        raise
    db.refresh(run)
    return run


def get_active_run(db: Session, hero: Hero) -> VeilRun | None:
    return db.execute(
        select(VeilRun).where(
            VeilRun.hero_id == hero.id, VeilRun.status == VeilRunStatus.IN_PROGRESS
        )
    ).scalar_one_or_none()


def claim_run(db: Session, run_id: uuid.UUID, hero_id: uuid.UUID) -> VeilRun:
    """Idempotently transition a resolved run to completed and apply its rewards.

    The conditional UPDATE (status='in_progress' AND resolves_at<=now) is the
    actual concurrency guarantee: only the caller whose UPDATE flips a row
    applies XP/loot, so two concurrent claims (e.g. two open tabs) never
    double-credit. A claim attempted before resolves_at simply updates 0 rows
    and returns the still-in-progress run unchanged. hero_id is folded into
    the same WHERE clause (not checked separately) so "you can't claim
    someone else's run" is a property of this function, not something every
    caller has to remember to check first.
    """
    now = datetime.now(timezone.utc)
    updated = db.execute(
        update(VeilRun)
        .where(
            VeilRun.id == run_id,
            VeilRun.hero_id == hero_id,
            VeilRun.status == VeilRunStatus.IN_PROGRESS,
            VeilRun.resolves_at <= now,
        )
        .values(status=VeilRunStatus.COMPLETED, claimed_at=now)
        .returning(VeilRun)
    ).scalar_one_or_none()

    if updated is not None:
        _apply_rewards(db, updated)
        db.commit()
        db.refresh(updated)
        return updated

    db.rollback()
    run = db.get(VeilRun, run_id)
    if run is None:
        raise ValueError(f"veil run {run_id} not found")
    return run


def _apply_rewards(db: Session, run: VeilRun) -> None:
    payload = run.result_payload or {}
    hero = db.get(Hero, run.hero_id)
    hero.xp += payload.get("xp_awarded", 0)
    hero_service.apply_level_ups(hero)

    if run.campaign_node_id is not None and payload.get("victory"):
        node = db.get(CampaignNode, run.campaign_node_id)
        if node is not None and node.order_index == hero.campaign_progress + 1:
            hero.campaign_progress = node.order_index

    for entry in payload.get("loot", []):
        slug = entry.get("item_template_slug")
        template = db.execute(
            select(ItemTemplate).where(ItemTemplate.slug == slug)
        ).scalar_one_or_none()
        if template is None:
            continue  # content may have been renamed/removed since the run resolved
        db.add(
            ItemInstance(
                template_id=template.id,
                owner_hero_id=run.hero_id,
                equipped_slot=None,
                source_veil_run_id=run.id,
            )
        )
