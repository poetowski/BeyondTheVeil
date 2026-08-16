import random
from dataclasses import dataclass, field
from typing import Any

from app.services.hero_service import HP_PER_VITALITY, compute_max_hp

# Tuned via simulation (see the playtesting pass that replaced these
# placeholders): thousands of simulated fights per candidate value, scored
# against a target win-rate curve as a function of hero-stat-vs-monster-stat
# ratio (roughly 5-10% at a 0.6-0.7x disadvantage, ~45-55% at parity,
# ~95%+ once meaningfully ahead) rather than the previous placeholder
# values, which produced win rates near 0% until the hero's stats reached
# ~2.5-6x a monster's - an unwinnable-feeling cliff, not a moderate one.
HIT_CHANCE_BASE = 0.5
HIT_CHANCE_K = 0.006
HIT_CHANCE_MIN = 0.10
HIT_CHANCE_MAX = 0.90
# Strength's physical-damage contribution is flat, not rolled: this many
# damage per strength point (e.g. 5 strength -> 20, 12 strength -> 48).
# A high multiplier (rather than a divisor <1, which integer floor-division
# can't express) is what keeps fights from dragging to MAX_ROUNDS - see the
# module docstring-adjacent comment above: shorter fights (fewer
# independent hit/miss rolls) are what keeps the win-rate curve smooth
# instead of a cliff, since many compounding rolls make even a slight edge
# converge toward a near-certain outcome (this is also why softening
# HIT_CHANCE_K alone, without raising damage, wasn't enough on its own).
STRENGTH_DAMAGE_MULTIPLIER = 4.0
# Mirrors STRENGTH_DAMAGE_MULTIPLIER for intelligence's spell-damage
# contribution (previously an implicit 1x multiplier: `max(1, intelligence)`
# - far too low relative to HP_PER_VITALITY-scaled HP pools, same root
# cause as strength's old divisor).
INTELLIGENCE_DAMAGE_MULTIPLIER = 4.0
MAX_ROUNDS = 30
MONSTER_STAT_VARIANCE = (0.85, 1.15)
# Hit-zone mechanic: only rolled when the monster hits the hero (monsters have
# no equipment to target zones on). Headshot always multiplies damage - it's
# not a chance-based crit, just a guaranteed consequence of the roll landing
# on the helmet zone.
ZONE_WEIGHTS = {"shield": 0.50, "armor": 0.35, "helmet": 0.15}
HEADSHOT_MULTIPLIER = 3
# A losing hero still keeps this fraction of the gold/XP the encounter
# would have paid out on a win - a consolation payout, not a full reward.
# Asymmetric on purpose (tuned via simulation, see hero_service.py's
# XP_CURVE_EXPONENT/TRAIN_STAT_* comment for the fuller picture): gold stays
# fairly generous so a losing streak still funds enough training to turn
# things around, while XP stays low so losing doesn't level the hero up -
# and into even tougher monster brackets - almost as fast as winning would.
DEFEAT_GOLD_RATIO = 0.35
DEFEAT_XP_RATIO = 0.05


@dataclass
class CombatResult:
    victory: bool
    monster_name: str | None = None
    log: list[dict[str, Any]] = field(default_factory=list)
    loot: list[dict[str, Any]] = field(default_factory=list)
    material_loot: list[dict[str, Any]] = field(default_factory=list)
    xp_awarded: int = 0
    gold_awarded: int = 0
    # Hero's HP right before this fight started (may be below max_hp if
    # regen hadn't fully caught up from a previous fight) and right after -
    # the difference is this fight's damage taken, distinct from the
    # hero's overall max_hp.
    hero_hp_before: int = 0
    hero_hp_after: int = 0
    monster_hp_after: int = 0
    # The monster's rolled stats/HP for this specific encounter - unlike the
    # outcome fields above, these are exposed to the client immediately (see
    # schemas/veil_run.py's ungated `encounter` field) so a combat screen can
    # show who the hero is fighting before the result reveals.
    monster_stats: dict[str, int] | None = None
    monster_max_hp: int = 0
    monster_slug: str | None = None
    # Flavor only, no mechanical effect - one specific level rolled from the
    # template's level_range for this encounter (see resolve()), re-rolled
    # every spawn.
    monster_level: int = 0
    # Display ranges for the monster's damage this encounter (rolled
    # strength/intelligence's flat contribution + its weapon_attack/
    # spell_attack range) - same shape as compute_damage_range()'s and
    # compute_spell_damage_range()'s hero-side output.
    monster_damage_min: int = 0
    monster_damage_max: int = 0
    monster_spell_damage_min: int = 0
    monster_spell_damage_max: int = 0
    monster_defense: int = 0


def compute_damage_range(
    strength: int, weapon_damage_range: tuple[int, int] | None
) -> tuple[int, int]:
    """Display-only physical damage range: strength's flat contribution
    (see STRENGTH_DAMAGE_MULTIPLIER and the per-hit formula in resolve())
    plus the weapon's roll, if any (0 if unarmed - strength alone still
    deals damage). min == max unless a weapon with a damage range is
    equipped, since strength itself is deterministic now, not rolled."""
    weapon_min, weapon_max = weapon_damage_range or (0, 0)
    strength_damage = max(1, round(strength * STRENGTH_DAMAGE_MULTIPLIER))
    return (strength_damage + weapon_min, strength_damage + weapon_max)


def compute_spell_damage_range(
    intelligence: int, spell_damage_range: tuple[int, int] | None
) -> tuple[int, int]:
    """Display-only spell damage range: intelligence's flat contribution
    (see INTELLIGENCE_DAMAGE_MULTIPLIER, floored at 1) plus the equipped
    spell skill's roll, if any (0 if none equipped - intelligence alone
    still deals damage). min == max unless a spell skill with a damage
    range is equipped."""
    spell_min, spell_max = spell_damage_range or (0, 0)
    intelligence_damage = max(1, round(intelligence * INTELLIGENCE_DAMAGE_MULTIPLIER))
    return (intelligence_damage + spell_min, intelligence_damage + spell_max)


def _hit_chance(attacker_stat: int, defender_stat: int) -> float:
    chance = HIT_CHANCE_BASE + (attacker_stat - defender_stat) * HIT_CHANCE_K
    return min(HIT_CHANCE_MAX, max(HIT_CHANCE_MIN, chance))


def _roll_monster_stats(rng: random.Random, base_stats: dict[str, int]) -> dict[str, int]:
    """Instances a monster's stats from its template, rolling each of the 6
    stats independently within MONSTER_STAT_VARIANCE so no two spawns of the
    same template play out identically."""
    return {
        stat: max(1, round(value * rng.uniform(*MONSTER_STAT_VARIANCE)))
        for stat, value in base_stats.items()
    }


def resolve(
    seed: int,
    hero_snapshot: dict[str, int],
    hero_base_stats: dict[str, int],
    encounter: dict[str, Any] | None,
    hero_current_hp: int | None = None,
    hero_weapon_damage_range: tuple[int, int] | None = None,
    hero_spell_damage_range: tuple[int, int] | None = None,
    hero_zone_defense: dict[str, int] | None = None,
    hero_bonus_max_hp: int = 0,
) -> CombatResult:
    """Deterministic, seed-reproducible combat in two phases: an opening
    spell exchange (intelligence for damage — flat, not rolled: see
    INTELLIGENCE_DAMAGE_MULTIPLIER — spirit-vs-spirit for hit chance,
    mirrors the physical hit-chance formula with magic's stat pair), then
    physical-only rounds (strength for damage — also flat: see
    STRENGTH_DAMAGE_MULTIPLIER — dexterity-vs-agility for hit chance).
    Vitality drives max HP throughout; the hero may start below max
    if `hero_current_hp` reflects unhealed damage from a previous fight
    (None means "start at full HP", used by every caller that doesn't track
    persistent HP).

    The monster's 6 stats are rolled once at the top of this function (see
    _roll_monster_stats), independently varying each stat within
    MONSTER_STAT_VARIANCE around the template's base_stats — so two spawns
    of the same MonsterTemplate are never identical. This roll consumes rng
    before any combat rolls below, so it's still fully reproducible from
    `seed`. Right after, a single monster_level is rolled uniformly from the
    encounter's monster_level_min/monster_level_max (the template's
    level_range) - flavor only, it has no effect on stats or combat math,
    and is re-rolled every spawn just like the 6 stats above.

    Turn order (initiative) is decided once, from *base* stats only (no item
    bonuses) — hero_base_stats vs the monster's (rolled) stats (monsters have
    no equipment, so theirs are inherently base already). Whoever's
    dexterity+agility sum is higher acts first, in both the spell exchange
    and the physical rounds that follow. Physical rounds alternate every
    single attack, one full round = each side attacks once.

    Gear affects damage asymmetrically, since only the hero can be equipped:
    when the hero lands a physical hit, hero_weapon_damage_range (if set)
    adds a random roll on top of the strength-based damage; when the hero
    lands a spell hit, hero_spell_damage_range does the same on top of the
    intelligence-based damage. When the monster lands a physical hit on the
    hero, a hit zone is rolled (see ZONE_WEIGHTS) and hero_zone_defense
    mitigates the damage for that zone; a helmet-zone hit always multiplies
    damage by HEADSHOT_MULTIPLIER before defense is subtracted. All default
    to "no gear equipped" so every existing caller is unaffected.

    Monsters have no equipment, but the encounter dict may carry flat
    weapon_attack_min/weapon_attack_max, spell_attack_min/spell_attack_max,
    and defense numbers (authored directly on MonsterTemplate, not
    item-derived - see combat/encounter.py) that play the same mechanical
    role gear plays for the hero: when the monster lands a physical hit,
    its weapon_attack range adds a roll on top of its strength-based
    damage, before the zone-defense mitigation above; when the monster
    lands a spell hit, its spell_attack range adds a roll on top of its
    intelligence-based damage, the same way hero_spell_damage_range does
    for the hero; when the hero lands a physical hit, the monster's flat
    defense reduces the damage the same way hero_zone_defense does, but
    unzoned (monsters have no equipment slots to split it across). All
    default to 0, so a monster with no authored attack/defense fights
    exactly as before these were added. Spell damage on either side is
    untouched by monster defense/hero_zone_defense - neither mitigates it.
    """
    if encounter is None:
        # No CombatResult field defaults to hero_current_hp here: hp_after
        # must equal hp_before exactly (no combat occurred) rather than the
        # dataclass default of 0, which would otherwise zero the hero's HP
        # on every veil attempt once they out-level all available content.
        hero_max_hp = compute_max_hp(hero_snapshot["vitality"], hero_bonus_max_hp)
        hero_hp = hero_max_hp if hero_current_hp is None else min(hero_current_hp, hero_max_hp)
        return CombatResult(
            victory=True,
            log=[{"message": "no monsters found for hero's level"}],
            hero_hp_before=hero_hp,
            hero_hp_after=hero_hp,
        )

    rng = random.Random(seed)
    monster_stats = _roll_monster_stats(rng, encounter["monster_stats"])
    monster_level_min = encounter.get("monster_level_min", 1)
    monster_level_max = encounter.get("monster_level_max", monster_level_min)
    monster_level = rng.randint(monster_level_min, monster_level_max)
    weapon_attack_min = encounter.get("weapon_attack_min", 0)
    weapon_attack_max = encounter.get("weapon_attack_max", 0)
    monster_defense = encounter.get("defense", 0)
    spell_attack_min = encounter.get("spell_attack_min", 0)
    spell_attack_max = encounter.get("spell_attack_max", 0)
    monster_damage_min, monster_damage_max = compute_damage_range(
        monster_stats["strength"], (weapon_attack_min, weapon_attack_max)
    )
    monster_spell_damage_min, monster_spell_damage_max = compute_spell_damage_range(
        monster_stats["intelligence"], (spell_attack_min, spell_attack_max)
    )

    hero_max_hp = compute_max_hp(hero_snapshot["vitality"], hero_bonus_max_hp)
    zone_defense = hero_zone_defense or {"shield": 0, "armor": 0, "helmet": 0}
    monster_max_hp = monster_stats["vitality"] * HP_PER_VITALITY
    hero_hp = hero_max_hp if hero_current_hp is None else min(hero_current_hp, hero_max_hp)
    hero_hp_before = hero_hp
    monster_hp = monster_max_hp

    hero_initiative = hero_base_stats["dexterity"] + hero_base_stats["agility"]
    monster_initiative = monster_stats["dexterity"] + monster_stats["agility"]
    order = ("hero", "monster") if hero_initiative >= monster_initiative else ("monster", "hero")

    log: list[dict[str, Any]] = []

    # Opening spell exchange: each side casts exactly once, in initiative
    # order, before any physical rounds begin. Intelligence is the magic
    # damage stat (mirrors strength - flat, not rolled), spirit is the
    # magic accuracy/resistance stat (mirrors dexterity/agility) — reuses
    # the same _hit_chance formula as the physical loop below.
    for actor in order:
        if hero_hp <= 0 or monster_hp <= 0:
            break

        if actor == "hero":
            attacker_intelligence = hero_snapshot["intelligence"]
            attacker_spirit = hero_snapshot["spirit"]
            defender_spirit = monster_stats["spirit"]
        else:
            attacker_intelligence = monster_stats["intelligence"]
            attacker_spirit = monster_stats["spirit"]
            defender_spirit = hero_snapshot["spirit"]

        hit = attacker_intelligence > 0 and rng.random() < _hit_chance(attacker_spirit, defender_spirit)
        damage = 0
        if hit:
            damage = max(1, round(attacker_intelligence * INTELLIGENCE_DAMAGE_MULTIPLIER))
            if actor == "hero":
                if hero_spell_damage_range is not None:
                    damage += rng.randint(*hero_spell_damage_range)
                monster_hp = max(0, monster_hp - damage)
            else:
                damage += rng.randint(spell_attack_min, spell_attack_max)
                hero_hp = max(0, hero_hp - damage)

        log.append(
            {
                "round": 0,
                "phase": "spell",
                "actor": actor,
                "hit": hit,
                "damage": damage,
                "defender_hp_remaining": monster_hp if actor == "hero" else hero_hp,
            }
        )

    round_number = 0
    while hero_hp > 0 and monster_hp > 0 and round_number < MAX_ROUNDS:
        round_number += 1
        for actor in order:
            if hero_hp <= 0 or monster_hp <= 0:
                break

            if actor == "hero":
                attacker_stat = hero_snapshot["dexterity"]
                defender_stat = monster_stats["agility"]
                attacker_strength = hero_snapshot["strength"]
            else:
                attacker_stat = monster_stats["dexterity"]
                defender_stat = hero_snapshot["agility"]
                attacker_strength = monster_stats["strength"]

            hit = rng.random() < _hit_chance(attacker_stat, defender_stat)
            damage = 0
            zone_hit = None
            if hit:
                damage = max(1, round(attacker_strength * STRENGTH_DAMAGE_MULTIPLIER))
                if actor == "hero":
                    if hero_weapon_damage_range is not None:
                        damage += rng.randint(*hero_weapon_damage_range)
                    damage = max(1, damage - monster_defense)
                    monster_hp = max(0, monster_hp - damage)
                else:
                    damage += rng.randint(weapon_attack_min, weapon_attack_max)
                    zone_hit = rng.choices(
                        list(ZONE_WEIGHTS.keys()), weights=list(ZONE_WEIGHTS.values()), k=1
                    )[0]
                    if zone_hit == "helmet":
                        damage *= HEADSHOT_MULTIPLIER
                    damage = max(1, damage - zone_defense.get(zone_hit, 0))
                    hero_hp = max(0, hero_hp - damage)

            log.append(
                {
                    "round": round_number,
                    "phase": "physical",
                    "actor": actor,
                    "hit": hit,
                    "damage": damage,
                    "zone": zone_hit,
                    "defender_hp_remaining": monster_hp if actor == "hero" else hero_hp,
                }
            )

    if monster_hp <= 0:
        victory = True
    elif hero_hp <= 0:
        victory = False
    else:
        # Round cap reached with both sides still standing: whoever dealt
        # more damage than they took wins the standoff (raw HP dealt/taken,
        # not normalized by either side's max HP - a huge HP pool "tanking"
        # a percentage-wise-small hit is still a big hit in absolute terms).
        damage_dealt_to_monster = monster_max_hp - monster_hp
        damage_dealt_to_hero = hero_max_hp - hero_hp
        victory = damage_dealt_to_monster >= damage_dealt_to_hero

    full_xp = sum(monster_stats.values()) if monster_stats else 0
    xp_awarded = full_xp if victory else round(full_xp * DEFEAT_XP_RATIO)
    rolled_gold = rng.randint(encounter.get("gold_min", 0), encounter.get("gold_max", 0))
    gold_awarded = rolled_gold if victory else round(rolled_gold * DEFEAT_GOLD_RATIO)

    loot: list[dict[str, Any]] = []
    loot_pool = encounter.get("loot_pool") or []
    if victory and loot_pool:
        # "No drop" is just another weighted option (None sentinel) alongside
        # the pool's items, so drop odds are tunable per monster via
        # no_drop_weight instead of a fixed global chance.
        no_drop_weight = encounter.get("no_drop_weight", 0)
        options: list[dict[str, Any] | None] = [*loot_pool, None]
        weights = [entry["drop_weight"] for entry in loot_pool] + [no_drop_weight]
        chosen = rng.choices(options, weights=weights, k=1)[0]
        if chosen is not None:
            loot.append(
                {"item_template_slug": chosen["item_template_slug"], "item_name": chosen["item_name"]}
            )

    material_loot: list[dict[str, Any]] = []
    material_pool = encounter.get("material_pool") or []
    if victory and material_pool:
        # Same "no drop" weighted-option approach as the item-loot roll above.
        no_material_drop_weight = encounter.get("no_material_drop_weight", 0)
        material_options: list[dict[str, Any] | None] = [*material_pool, None]
        material_weights = [entry["drop_weight"] for entry in material_pool] + [no_material_drop_weight]
        chosen_material = rng.choices(material_options, weights=material_weights, k=1)[0]
        if chosen_material is not None:
            material_loot.append(
                {
                    "material_template_slug": chosen_material["material_template_slug"],
                    "material_name": chosen_material["material_name"],
                    "quantity": 1,
                }
            )

    return CombatResult(
        victory=victory,
        monster_name=encounter["monster_name"],
        log=log,
        loot=loot,
        material_loot=material_loot,
        xp_awarded=xp_awarded,
        gold_awarded=gold_awarded,
        hero_hp_before=hero_hp_before,
        hero_hp_after=hero_hp,
        monster_hp_after=monster_hp,
        monster_stats=monster_stats,
        monster_max_hp=monster_max_hp,
        monster_slug=encounter.get("monster_slug"),
        monster_level=monster_level,
        monster_damage_min=monster_damage_min,
        monster_damage_max=monster_damage_max,
        monster_spell_damage_min=monster_spell_damage_min,
        monster_spell_damage_max=monster_spell_damage_max,
        monster_defense=monster_defense,
    )
