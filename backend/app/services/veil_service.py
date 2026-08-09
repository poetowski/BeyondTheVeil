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
from app.models.material import MaterialInstance, MaterialTemplate
from app.models.veil_run import VeilRun, VeilRunStatus
from app.services import hero_service
from app.services.combat import encounter as encounter_service
from app.services.combat import engine as combat_engine


class VeilServiceError(Exception):
    """Base class for veil-entry failures."""


class HeroTooWoundedError(VeilServiceError):
    pass


def check_not_too_wounded(db: Session, hero: Hero) -> None:
    """Raises HeroTooWoundedError if the hero's regenerated current HP is
    <= 0. Public: called both internally (enter_veil/enter_campaign_encounter)
    and by campaign_service, which needs to check this *before* deducting a
    node's gold cost rather than after."""
    equipped_items = hero_service.get_equipped_items(db, hero)
    effective_stats = hero_service.compute_effective_stats(hero, equipped_items)
    bonus_max_hp = hero_service.compute_bonus_max_hp(equipped_items)
    current_hp = hero_service.compute_current_hp(
        hero, effective_stats["vitality"], bonus_max_hp=bonus_max_hp
    )
    if current_hp <= 0:
        raise HeroTooWoundedError("hero is too wounded to enter the veil")


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
    check_not_too_wounded(db, hero)

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
    check_not_too_wounded(db, hero)

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
    bonus_max_hp = hero_service.compute_bonus_max_hp(equipped_items)
    weapon_damage_range = hero_service.compute_weapon_damage_range(equipped_items)
    zone_defense = hero_service.compute_zone_defense(equipped_items)

    started_at = datetime.now(timezone.utc)
    duration_seconds = settings.veil_duration_seconds
    resolves_at = started_at + timedelta(seconds=duration_seconds)

    hero_current_hp = hero_service.compute_current_hp(
        hero, effective_stats["vitality"], bonus_max_hp=bonus_max_hp, now=started_at
    )
    result = combat_engine.resolve(
        seed=seed,
        hero_snapshot=effective_stats,
        hero_base_stats=base_stats,
        encounter=encounter,
        hero_current_hp=hero_current_hp,
        hero_weapon_damage_range=weapon_damage_range,
        hero_zone_defense=zone_defense,
        hero_bonus_max_hp=bonus_max_hp,
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
    hero_service.apply_xp(hero, payload.get("xp_awarded", 0))
    hero.gold += payload.get("gold_awarded", 0)

    if "hero_hp_after" in payload:
        # Anchored to when combat actually concluded (resolves_at), not
        # whenever the player happens to claim - otherwise a late claim
        # would grant bonus free regen for the delay. Guarded by key
        # presence so runs created before this field existed don't crash.
        hero.current_hp = payload["hero_hp_after"]
        hero.hp_updated_at = run.resolves_at

    if run.campaign_node_id is not None and payload.get("victory"):
        node = db.get(CampaignNode, run.campaign_node_id)
        if node is not None and node.order_index == hero.campaign_progress + 1:
            hero.campaign_progress = node.order_index

    loot_entries = payload.get("loot", [])
    loot_skipped: list[dict] = []
    if loot_entries:
        current_count = hero_service.get_backpack_used_capacity(db, hero)
        for entry in loot_entries:
            slug = entry.get("item_template_slug")
            template = db.execute(
                select(ItemTemplate).where(ItemTemplate.slug == slug)
            ).scalar_one_or_none()
            if template is None:
                continue  # content may have been renamed/removed since the run resolved
            if current_count >= hero.inventory_capacity:
                loot_skipped.append(entry)
                continue
            db.add(
                ItemInstance(
                    template_id=template.id,
                    owner_hero_id=run.hero_id,
                    equipped_slot=None,
                    source_veil_run_id=run.id,
                )
            )
            current_count += 1

    if loot_skipped:
        # Reassign (don't mutate result_payload in place) so SQLAlchemy
        # detects the JSONB column as dirty.
        run.result_payload = {**payload, "loot_skipped": loot_skipped}

    material_loot_entries = payload.get("material_loot", [])
    for entry in material_loot_entries:
        slug = entry.get("material_template_slug")
        quantity = entry.get("quantity", 1)
        template = db.execute(
            select(MaterialTemplate).where(MaterialTemplate.slug == slug)
        ).scalar_one_or_none()
        if template is None:
            continue  # content may have been renamed/removed since the run resolved
        existing_stack = (
            db.execute(
                select(MaterialInstance).where(
                    MaterialInstance.owner_hero_id == hero.id,
                    MaterialInstance.template_id == template.id,
                )
            )
            .scalars()
            .first()
        )
        if existing_stack is not None:
            existing_stack.quantity += quantity
            db.add(existing_stack)
        else:
            db.add(
                MaterialInstance(
                    template_id=template.id,
                    owner_hero_id=hero.id,
                    quantity=quantity,
                    source_veil_run_id=run.id,
                )
            )
