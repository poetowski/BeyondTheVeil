import dataclasses
import random
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.hero import Hero
from app.models.item import ItemInstance
from app.models.veil_run import VeilRun, VeilRunStatus
from app.services import hero_service
from app.services.combat import engine as combat_engine

DEFAULT_DURATION_SECONDS = 5 * 60


def enter_veil(db: Session, hero: Hero) -> VeilRun:
    """Start a veil run, resolving combat immediately but revealing nothing
    until `resolves_at` has passed (see schemas.veil_run.is_visible).

    Safe under a double-submit: the partial unique index on
    veil_runs(hero_id) WHERE status='in_progress' is the actual guarantee;
    the pre-check here just avoids doing wasted work in the common case.
    """
    existing = get_active_run(db, hero)
    if existing is not None:
        return existing

    equipped_items = (
        db.execute(
            select(ItemInstance).where(
                ItemInstance.owner_hero_id == hero.id,
                ItemInstance.equipped_slot.is_not(None),
            )
        )
        .scalars()
        .all()
    )
    effective_stats = hero_service.compute_effective_stats(hero, equipped_items)

    seed = random.getrandbits(63)
    started_at = datetime.now(timezone.utc)
    resolves_at = started_at + timedelta(seconds=DEFAULT_DURATION_SECONDS)

    # encounter generation (which monsters/loot pool appear) is procedural-generation
    # content out of scope for the core data model; {} is a placeholder encounter.
    result = combat_engine.resolve(seed=seed, hero_snapshot=effective_stats, encounter={})

    run = VeilRun(
        hero_id=hero.id,
        seed=seed,
        status=VeilRunStatus.IN_PROGRESS,
        started_at=started_at,
        duration_seconds=DEFAULT_DURATION_SECONDS,
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


def claim_run(db: Session, run_id: uuid.UUID) -> VeilRun:
    """Idempotently transition a resolved run to completed and apply its rewards.

    The conditional UPDATE (status='in_progress' AND resolves_at<=now) is the
    actual concurrency guarantee: only the caller whose UPDATE flips a row
    applies XP/loot, so two concurrent claims (e.g. two open tabs) never
    double-credit. A claim attempted before resolves_at simply updates 0 rows
    and returns the still-in-progress run unchanged.
    """
    now = datetime.now(timezone.utc)
    updated = db.execute(
        update(VeilRun)
        .where(
            VeilRun.id == run_id,
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
    # Materializing `loot` entries into ItemInstance rows depends on procedural
    # loot-generation internals that are out of scope for the core data model;
    # this is the integration point future work plugs into.
