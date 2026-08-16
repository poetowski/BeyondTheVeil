import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.avatar import AvatarTemplate, HeroAvatarUnlock
from app.models.consumable import ConsumableInstance
from app.models.hero import Hero
from app.models.item import EquipmentSlot, ItemInstance, ItemTemplate
from app.models.material import MaterialInstance
from app.models.rune import RuneInstance

STAT_NAMES = ("strength", "dexterity", "intelligence", "vitality", "agility", "spirit")

# The existing tier-1 gear set (see seed_dev_data.py's ITEM_TEMPLATES),
# granted equipped to every new hero - see grant_starter_gear. Monsters
# already carry a flat weapon_attack/defense from level 1 (see
# combat/engine.py); an unarmed, unarmored hero has 0 in both, which makes
# even the earliest monsters nearly unwinnable. slugs, not names, since
# ItemTemplate.slug is the lookup key everywhere else in this codebase.
STARTER_GEAR_SLUGS = ("wooden-stick", "wooden-shield", "leather-helm", "leather-robe")

HP_PER_VITALITY = 10
BASE_HP = 50
BASELINE_STAT_VALUE = 10

# Tuned via simulation (see the playtesting pass that replaced these
# placeholders, same one that tuned combat/engine.py's formula constants).
# A hero needs all 6 stats to climb roughly together to stay viable (every
# stat matters for either hit chance, damage, or HP), so the previous
# TRAIN_STAT_EXPONENT=1.5/BASE_COST=10 compounded across 6 independent
# power-1.5 curves into a gold cost monster reward income could never catch
# up with - simulated play never escaped a near-0% win rate no matter how
# well it played. XP_CURVE_EXPONENT raised slightly so leveling (which gates
# which, often much tougher, monsters a hero can be matched against - see
# combat/encounter.py's select_encounter) doesn't outrun gold-funded
# training, especially since a defeat still grants partial XP (see
# combat/engine.py's DEFEAT_XP_RATIO).
XP_CURVE_BASE = 100
XP_CURVE_EXPONENT = 1.6
TRAIN_STAT_BASE_COST = 5
TRAIN_STAT_EXPONENT = 1.05

# Selling anything owned (item/material/consumable/rune) refunds this
# fraction of its template's price, rounded. Buying costs the full price -
# see shop_service.
SHOP_SELL_PRICE_RATIO = 0.25


class HeroServiceError(Exception):
    """Base class for hero-mutation failures (equip, unequip, stat training)."""


class ItemNotFoundError(HeroServiceError):
    pass


class ItemNotOwnedError(HeroServiceError):
    pass


class LevelRequirementNotMetError(HeroServiceError):
    pass


class UnknownStatError(HeroServiceError):
    pass


class InsufficientGoldError(HeroServiceError):
    pass


class RuneNotFoundError(HeroServiceError):
    pass


class RuneNotOwnedError(HeroServiceError):
    pass


class RuneAlreadyAppliedError(HeroServiceError):
    pass


class ItemEquippedError(HeroServiceError):
    pass


class MaterialNotFoundError(HeroServiceError):
    pass


class MaterialNotOwnedError(HeroServiceError):
    pass


class ConsumableNotFoundError(HeroServiceError):
    """Distinct from crafting_service.ConsumableNotFoundError -
    crafting_service already imports hero_service, so hero_service can't
    import crafting_service's version back without a circular import."""

    pass


class ConsumableNotOwnedError(HeroServiceError):
    pass


class AvatarNotFoundError(HeroServiceError):
    pass


class AvatarNotUnlockedError(HeroServiceError):
    pass


def compute_base_stats(hero: Hero) -> dict[str, int]:
    return {stat: getattr(hero, stat) for stat in STAT_NAMES}


def compute_stat_bonuses(hero: Hero, equipped_items: list[ItemInstance]) -> dict[str, int]:
    """Bonuses from every currently-equipped item (weapon, armor, spell skill, etc.),
    isolated from base stats so base + bonus == effective by construction."""
    bonuses = {stat: 0 for stat in STAT_NAMES}
    for item in equipped_items:
        if item.equipped_slot is None:
            continue
        sources = [item.template.base_stats, item.rolled_stats]
        if item.rune_template is not None:
            sources.append(item.rune_template.stat_bonuses)
        for source in sources:
            if not source:
                continue
            for stat, bonus in source.items():
                if stat in bonuses:
                    bonuses[stat] += bonus
    return bonuses


def compute_effective_stats(hero: Hero, equipped_items: list[ItemInstance]) -> dict[str, int]:
    """Base hero stats plus bonuses from every currently-equipped item."""
    base = compute_base_stats(hero)
    bonuses = compute_stat_bonuses(hero, equipped_items)
    return {stat: base[stat] + bonuses[stat] for stat in STAT_NAMES}


def compute_max_hp(effective_vitality: int, bonus_max_hp: int = 0) -> int:
    """Placeholder formula; combat balance is a separate future task.
    bonus_max_hp is a flat addition from equipped gear (e.g. a ring),
    separate from vitality-derived HP - defaults to 0 so every pre-existing
    caller that doesn't track gear bonuses is unaffected."""
    return BASE_HP + effective_vitality * HP_PER_VITALITY + bonus_max_hp


def compute_current_hp(
    hero: Hero, effective_vitality: int, *, bonus_max_hp: int = 0, now: datetime | None = None
) -> int:
    """Lazily regenerated HP: no background job, just derives the current
    value from the last-persisted current_hp/hp_updated_at plus elapsed
    time. Read-only — callers that want to persist the regenerated value
    must do so explicitly (see veil_service._apply_rewards)."""
    now = now or datetime.now(timezone.utc)
    max_hp = compute_max_hp(effective_vitality, bonus_max_hp)
    elapsed_seconds = max(0.0, (now - hero.hp_updated_at).total_seconds())
    regen_per_second = max_hp / settings.hp_regen_seconds_to_full
    return min(max_hp, round(hero.current_hp + elapsed_seconds * regen_per_second))


def compute_weapon_damage_range(equipped_items: list[ItemInstance]) -> tuple[int, int] | None:
    """The equipped weapon's (damage_min, damage_max), or None if unarmed or
    the equipped weapon has no damage range set."""
    for item in equipped_items:
        if item.equipped_slot != EquipmentSlot.WEAPON:
            continue
        template = item.template
        if template.damage_min is not None and template.damage_max is not None:
            return (template.damage_min, template.damage_max)
    return None


def compute_spell_damage_range(equipped_items: list[ItemInstance]) -> tuple[int, int] | None:
    """The equipped spell skill's (spell_damage_min, spell_damage_max), or
    None if none equipped or it has no spell damage range set."""
    for item in equipped_items:
        if item.equipped_slot != EquipmentSlot.SPELL_SKILL:
            continue
        template = item.template
        if template.spell_damage_min is not None and template.spell_damage_max is not None:
            return (template.spell_damage_min, template.spell_damage_max)
    return None


def compute_zone_defense(equipped_items: list[ItemInstance]) -> dict[str, int]:
    """Flat physical-damage defense per hit zone, from whatever's equipped
    in the shield/armor/helmet slots. Zero for an empty slot."""
    defense = {"shield": 0, "armor": 0, "helmet": 0}
    for item in equipped_items:
        slot = item.equipped_slot.value if item.equipped_slot else None
        if slot in defense:
            defense[slot] += item.template.defense
    return defense


def compute_bonus_max_hp(equipped_items: list[ItemInstance]) -> int:
    """Flat max-HP bonus summed across every equipped item (not
    slot-restricted, so it isn't tied to amulets specifically)."""
    return sum(item.template.bonus_max_hp for item in equipped_items if item.equipped_slot is not None)


def xp_required_for_level(level: int) -> int:
    """XP needed to advance from `level` to `level + 1`."""
    return round(level**XP_CURVE_EXPONENT * XP_CURVE_BASE)


def apply_xp(hero: Hero, xp_gained: int) -> int:
    """Adds XP to the hero, leveling up (possibly multiple times) whenever the
    threshold for the hero's current level is reached. xp is a rolling
    progress-to-next-level counter, not lifetime total: it resets to the
    leftover remainder on every level-up. Level is purely a content gate here
    — it does not itself change any stat. Returns the number of levels gained.
    """
    hero.xp += xp_gained
    levels_gained = 0
    while hero.xp >= xp_required_for_level(hero.level):
        hero.xp -= xp_required_for_level(hero.level)
        hero.level += 1
        levels_gained += 1
    return levels_gained


def train_stat_cost(current_value: int) -> int:
    """Gold cost to raise a stat by one point from its current value.

    A power curve, not a linear one: each point already trained above
    baseline raises the cost of the next by TRAIN_STAT_EXPONENT, so early
    points are cheap but late ones become a serious gold sink rather than a
    grind (e.g. base cost 10: 10, 28, 52, 80, 112, ... for points 0-4 above
    baseline).
    """
    points_above_baseline = max(0, current_value - BASELINE_STAT_VALUE)
    return round(TRAIN_STAT_BASE_COST * (points_above_baseline + 1) ** TRAIN_STAT_EXPONENT)


def train_stat(db: Session, hero: Hero, stat: str) -> Hero:
    if stat not in STAT_NAMES:
        raise UnknownStatError(f"unknown stat: {stat}")

    cost = train_stat_cost(getattr(hero, stat))
    if hero.gold < cost:
        raise InsufficientGoldError("not enough gold to train this stat")

    hero.gold -= cost
    setattr(hero, stat, getattr(hero, stat) + 1)
    db.add(hero)
    db.commit()
    db.refresh(hero)
    return hero


def is_avatar_unlocked(db: Session, hero: Hero, avatar: AvatarTemplate) -> bool:
    """Two independent gates, both must pass:
    - level_requirement: hero.level must meet it (no purchase involved -
      e.g. Warrior Avatar just needs level 10).
    - price/unlock_hint: a price=0 avatar with no unlock_hint is free once
      the level gate above passes; a price>0 avatar, or a price=0 avatar
      with unlock_hint set (gated behind a specific action instead of
      gold or level - see AvatarTemplate's docstring), additionally needs
      a HeroAvatarUnlock row (see unlock_avatar and grant_avatar_unlock).
    """
    if hero.level < avatar.level_requirement:
        return False
    if avatar.price == 0 and avatar.unlock_hint is None:
        return True
    existing = db.execute(
        select(HeroAvatarUnlock).where(
            HeroAvatarUnlock.hero_id == hero.id,
            HeroAvatarUnlock.avatar_template_id == avatar.id,
        )
    ).scalar_one_or_none()
    return existing is not None


def grant_avatar_unlock(db: Session, hero: Hero, avatar_slug: str) -> None:
    """Idempotently grants a hero a HeroAvatarUnlock row for an
    unlock_hint-gated avatar (see AvatarTemplate's docstring), bypassing
    gold/unlock_avatar entirely - for game actions that unlock an avatar
    directly (e.g. crafting_service.use_consumable's Herbalist Hell
    special case) rather than a player purchase. No-op if the avatar
    doesn't exist or the hero already has it unlocked - safe to call on
    every use of whatever action triggers it, not just the first. Does
    not commit; the caller controls the transaction."""
    avatar = db.execute(
        select(AvatarTemplate).where(AvatarTemplate.slug == avatar_slug)
    ).scalar_one_or_none()
    if avatar is None:
        return
    existing = db.execute(
        select(HeroAvatarUnlock).where(
            HeroAvatarUnlock.hero_id == hero.id,
            HeroAvatarUnlock.avatar_template_id == avatar.id,
        )
    ).scalar_one_or_none()
    if existing is not None:
        return
    db.add(HeroAvatarUnlock(hero_id=hero.id, avatar_template_id=avatar.id))


def unlock_avatar(db: Session, hero: Hero, avatar_slug: str) -> Hero:
    """Idempotent - a no-op (no charge) if the avatar is free/already
    unlocked, same spirit as every other "safe to call twice" mutation in
    this module. Only price>0 avatars are actually purchasable here - a
    price=0 avatar that isn't unlocked yet is gated by level_requirement
    instead, which no amount of gold bypasses."""
    avatar = db.execute(
        select(AvatarTemplate).where(AvatarTemplate.slug == avatar_slug)
    ).scalar_one_or_none()
    if avatar is None:
        raise AvatarNotFoundError(f"unknown avatar: {avatar_slug}")

    if is_avatar_unlocked(db, hero, avatar):
        return hero

    if avatar.price == 0:
        detail = avatar.unlock_hint or f"requires level {avatar.level_requirement}"
        raise AvatarNotUnlockedError(f"avatar not purchasable ({detail}): {avatar_slug}")

    if hero.gold < avatar.price:
        raise InsufficientGoldError("not enough gold to unlock this avatar")

    hero.gold -= avatar.price
    db.add(hero)
    db.add(HeroAvatarUnlock(hero_id=hero.id, avatar_template_id=avatar.id))
    db.commit()
    db.refresh(hero)
    return hero


def set_avatar(db: Session, hero: Hero, avatar_slug: str) -> Hero:
    avatar = db.execute(
        select(AvatarTemplate).where(AvatarTemplate.slug == avatar_slug)
    ).scalar_one_or_none()
    if avatar is None:
        raise AvatarNotFoundError(f"unknown avatar: {avatar_slug}")
    if not is_avatar_unlocked(db, hero, avatar):
        raise AvatarNotUnlockedError(f"avatar not unlocked: {avatar_slug}")

    hero.avatar_template_id = avatar.id
    db.add(hero)
    db.commit()
    db.refresh(hero)
    return hero


def equip_item(db: Session, hero: Hero, item_id: uuid.UUID) -> ItemInstance:
    """Equips an owned item, auto-unequipping whatever currently occupies its
    slot (a single action swaps gear rather than requiring an explicit
    unequip first). The DB's partial unique index on (owner_hero_id,
    equipped_slot) remains the actual invariant guarantee; this just keeps a
    normal equip from tripping over it."""
    item = db.get(ItemInstance, item_id)
    if item is None:
        raise ItemNotFoundError(f"item {item_id} not found")
    if item.owner_hero_id != hero.id:
        raise ItemNotOwnedError("hero does not own this item")
    if hero.level < item.template.level_requirement:
        raise LevelRequirementNotMetError("hero level is too low to equip this item")

    slot = item.template.slot
    currently_equipped = db.execute(
        select(ItemInstance).where(
            ItemInstance.owner_hero_id == hero.id,
            ItemInstance.equipped_slot == slot,
        )
    ).scalar_one_or_none()
    if currently_equipped is not None and currently_equipped.id != item.id:
        currently_equipped.equipped_slot = None
        db.add(currently_equipped)
        # Flush the clear before setting the new slot: SQLAlchemy's unit of
        # work does not guarantee these two UPDATEs hit the DB in the order
        # their attributes were set (it may batch same-table UPDATEs via
        # executemany in an unspecified order), and the partial unique index
        # is checked immediately (not deferrable) — so without this, the new
        # item's UPDATE can occasionally be sent before the old item's clear
        # and collide with it.
        db.flush()

    item.equipped_slot = slot
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def unequip_item(db: Session, hero: Hero, item_id: uuid.UUID) -> ItemInstance:
    item = db.get(ItemInstance, item_id)
    if item is None:
        raise ItemNotFoundError(f"item {item_id} not found")
    if item.owner_hero_id != hero.id:
        raise ItemNotOwnedError("hero does not own this item")

    item.equipped_slot = None
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def apply_rune(db: Session, hero: Hero, item_id: uuid.UUID, rune_instance_id: uuid.UUID) -> ItemInstance:
    """Permanently fuses one unit of an owned, unattached rune stack onto an
    owned item. There is no reverse operation - once item.rune_template_id
    is set it is never cleared."""
    item = db.get(ItemInstance, item_id)
    if item is None:
        raise ItemNotFoundError(f"item {item_id} not found")
    if item.owner_hero_id != hero.id:
        raise ItemNotOwnedError("hero does not own this item")
    if item.rune_template_id is not None:
        raise RuneAlreadyAppliedError("item already has a rune applied")

    rune = db.get(RuneInstance, rune_instance_id)
    if rune is None:
        raise RuneNotFoundError(f"rune {rune_instance_id} not found")
    if rune.owner_hero_id != hero.id:
        raise RuneNotOwnedError("hero does not own this rune")

    item.rune_template_id = rune.template_id
    db.add(item)

    rune.quantity -= 1
    if rune.quantity == 0:
        db.delete(rune)
    else:
        db.add(rune)

    db.commit()
    db.refresh(item)
    return item


def sell_item(db: Session, hero: Hero, item_id: uuid.UUID) -> int:
    """Sells one owned, unequipped item for SHOP_SELL_PRICE_RATIO of its
    template's price (rounded). Equipped items must be unequipped first -
    see ItemEquippedError."""
    item = db.get(ItemInstance, item_id)
    if item is None:
        raise ItemNotFoundError(f"item {item_id} not found")
    if item.owner_hero_id != hero.id:
        raise ItemNotOwnedError("hero does not own this item")
    if item.equipped_slot is not None:
        raise ItemEquippedError("unequip this item before selling it")

    gold_gained = round(item.template.price * SHOP_SELL_PRICE_RATIO)
    hero.gold += gold_gained
    db.add(hero)
    db.delete(item)
    db.commit()
    db.refresh(hero)
    return gold_gained


def sell_material(db: Session, hero: Hero, material_instance_id: uuid.UUID) -> int:
    """Sells one unit from an owned material stack."""
    material = db.get(MaterialInstance, material_instance_id)
    if material is None:
        raise MaterialNotFoundError(f"material {material_instance_id} not found")
    if material.owner_hero_id != hero.id:
        raise MaterialNotOwnedError("hero does not own this material")

    gold_gained = round(material.template.price * SHOP_SELL_PRICE_RATIO)
    hero.gold += gold_gained
    material.quantity -= 1
    if material.quantity == 0:
        db.delete(material)
    else:
        db.add(material)
    db.add(hero)
    db.commit()
    db.refresh(hero)
    return gold_gained


def sell_consumable(db: Session, hero: Hero, consumable_instance_id: uuid.UUID) -> int:
    """Sells one unit from an owned consumable stack. Mirrors sell_material."""
    consumable = db.get(ConsumableInstance, consumable_instance_id)
    if consumable is None:
        raise ConsumableNotFoundError(f"consumable {consumable_instance_id} not found")
    if consumable.owner_hero_id != hero.id:
        raise ConsumableNotOwnedError("hero does not own this consumable")

    gold_gained = round(consumable.template.price * SHOP_SELL_PRICE_RATIO)
    hero.gold += gold_gained
    consumable.quantity -= 1
    if consumable.quantity == 0:
        db.delete(consumable)
    else:
        db.add(consumable)
    db.add(hero)
    db.commit()
    db.refresh(hero)
    return gold_gained


def sell_rune(db: Session, hero: Hero, rune_instance_id: uuid.UUID) -> int:
    """Sells one unit from an owned, unattached rune stack. Mirrors
    sell_material. A rune already fused to an item isn't a RuneInstance row
    (see apply_rune) so there's nothing to sell there."""
    rune = db.get(RuneInstance, rune_instance_id)
    if rune is None:
        raise RuneNotFoundError(f"rune {rune_instance_id} not found")
    if rune.owner_hero_id != hero.id:
        raise RuneNotOwnedError("hero does not own this rune")

    gold_gained = round(rune.template.price * SHOP_SELL_PRICE_RATIO)
    hero.gold += gold_gained
    rune.quantity -= 1
    if rune.quantity == 0:
        db.delete(rune)
    else:
        db.add(rune)
    db.add(hero)
    db.commit()
    db.refresh(hero)
    return gold_gained


def grant_starter_gear(db: Session, hero: Hero) -> None:
    """Equips the tier-1 starter kit (see STARTER_GEAR_SLUGS) into any of
    those slots the hero doesn't already have something equipped in.
    Idempotent and safe to call on an existing hero, not just a brand-new
    one (see the matching migration backfill for already-created heroes) -
    it only fills empty slots, never replaces gear the hero already has.
    Does not commit; the caller controls the transaction."""
    occupied_slots = {item.equipped_slot for item in get_equipped_items(db, hero)}
    for slug in STARTER_GEAR_SLUGS:
        template = db.execute(select(ItemTemplate).where(ItemTemplate.slug == slug)).scalar_one_or_none()
        if template is None or template.slot in occupied_slots:
            continue
        db.add(ItemInstance(template_id=template.id, owner_hero_id=hero.id, equipped_slot=template.slot))


def get_equipped_items(db: Session, hero: Hero) -> list[ItemInstance]:
    return (
        db.execute(
            select(ItemInstance).where(
                ItemInstance.owner_hero_id == hero.id,
                ItemInstance.equipped_slot.is_not(None),
            )
        )
        .scalars()
        .all()
    )


def get_owned_items(db: Session, hero: Hero) -> list[ItemInstance]:
    """Everything the hero owns, equipped or not (i.e. the full backpack)."""
    return (
        db.execute(
            select(ItemInstance)
            .where(ItemInstance.owner_hero_id == hero.id)
            .order_by(ItemInstance.acquired_at.desc())
        )
        .scalars()
        .all()
    )


def get_owned_materials(db: Session, hero: Hero) -> list[MaterialInstance]:
    """Every crafting-material stack the hero owns."""
    return (
        db.execute(
            select(MaterialInstance)
            .where(MaterialInstance.owner_hero_id == hero.id)
            .order_by(MaterialInstance.acquired_at.desc())
        )
        .scalars()
        .all()
    )


def get_owned_consumables(db: Session, hero: Hero) -> list[ConsumableInstance]:
    """Every consumable (e.g. elixir) stack the hero owns."""
    return (
        db.execute(
            select(ConsumableInstance)
            .where(ConsumableInstance.owner_hero_id == hero.id)
            .order_by(ConsumableInstance.acquired_at.desc())
        )
        .scalars()
        .all()
    )


def get_owned_runes(db: Session, hero: Hero) -> list[RuneInstance]:
    """Every unattached rune stack the hero owns (not yet fused to an item)."""
    return (
        db.execute(
            select(RuneInstance)
            .where(RuneInstance.owner_hero_id == hero.id)
            .order_by(RuneInstance.acquired_at.desc())
        )
        .scalars()
        .all()
    )


def get_backpack_used_capacity(db: Session, hero: Hero) -> int:
    """How much of hero.inventory_capacity is currently used. Items are
    one-slot-each; consumables and unattached rune stacks count by quantity
    (a stack of 5 elixirs uses 5 slots, not 1) - all share the same cap."""
    items_count = len(get_owned_items(db, hero))
    consumables_count = sum(c.quantity for c in get_owned_consumables(db, hero))
    runes_count = sum(r.quantity for r in get_owned_runes(db, hero))
    return items_count + consumables_count + runes_count


def get_leaderboard(db: Session, limit: int = 10) -> list[Hero]:
    """Top heroes by level, highest first. Ties broken by xp (the rolling
    progress-to-next-level counter) so heroes closer to their next level
    rank above ones further behind at the same level."""
    return (
        db.execute(
            select(Hero).order_by(Hero.level.desc(), Hero.xp.desc()).limit(limit)
        )
        .scalars()
        .all()
    )
