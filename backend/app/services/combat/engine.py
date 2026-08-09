import math
import random
from dataclasses import dataclass, field
from typing import Any

from app.services.hero_service import HP_PER_VITALITY, compute_max_hp

# Placeholder formulas/constants — combat balance is a separate future task.
HIT_CHANCE_BASE = 0.5
HIT_CHANCE_K = 0.04
HIT_CHANCE_MIN = 0.10
HIT_CHANCE_MAX = 0.90
DAMAGE_VARIANCE = (0.8, 1.2)
MAX_ROUNDS = 30
DROP_CHANCE = 0.5
MATERIAL_DROP_CHANCE = 0.5
GOLD_PER_VICTORY = 10
SPELL_DAMAGE_MULTIPLIER = 3  # intelligence contributes 3x the damage per point that strength does
MONSTER_STAT_VARIANCE = (0.85, 1.15)


@dataclass
class CombatResult:
    victory: bool
    monster_name: str | None = None
    log: list[dict[str, Any]] = field(default_factory=list)
    loot: list[dict[str, Any]] = field(default_factory=list)
    material_loot: list[dict[str, Any]] = field(default_factory=list)
    xp_awarded: int = 0
    gold_awarded: int = 0
    hero_hp_after: int = 0


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
) -> CombatResult:
    """Deterministic, seed-reproducible combat in two phases: an opening
    spell exchange (intelligence for damage — at SPELL_DAMAGE_MULTIPLIER
    per point vs. strength's 1x, spirit-vs-spirit for hit chance — mirrors
    the physical hit-chance formula with magic's stat pair), then
    physical-only rounds (strength for damage, dexterity-vs-agility for hit
    chance). Vitality drives max HP throughout; the hero may start below max
    if `hero_current_hp` reflects unhealed damage from a previous fight
    (None means "start at full HP", used by every caller that doesn't track
    persistent HP).

    The monster's 6 stats are rolled once at the top of this function (see
    _roll_monster_stats), independently varying each stat within
    MONSTER_STAT_VARIANCE around the template's base_stats — so two spawns
    of the same MonsterTemplate are never identical. This roll consumes rng
    before any combat rolls below, so it's still fully reproducible from
    `seed`.

    Turn order (initiative) is decided once, from *base* stats only (no item
    bonuses) — hero_base_stats vs the monster's (rolled) stats (monsters have
    no equipment, so theirs are inherently base already). Whoever's
    dexterity+agility sum is higher acts first, in both the spell exchange
    and the physical rounds that follow. Physical rounds alternate every
    single attack, one full round = each side attacks once.
    """
    if encounter is None:
        return CombatResult(victory=True, log=[{"message": "no monsters found for hero's level"}])

    rng = random.Random(seed)
    monster_stats = _roll_monster_stats(rng, encounter["monster_stats"])

    hero_max_hp = compute_max_hp(hero_snapshot["vitality"])
    monster_max_hp = monster_stats["vitality"] * HP_PER_VITALITY
    hero_hp = hero_max_hp if hero_current_hp is None else min(hero_current_hp, hero_max_hp)
    monster_hp = monster_max_hp

    hero_initiative = hero_base_stats["dexterity"] + hero_base_stats["agility"]
    monster_initiative = monster_stats["dexterity"] + monster_stats["agility"]
    order = ("hero", "monster") if hero_initiative >= monster_initiative else ("monster", "hero")

    log: list[dict[str, Any]] = []

    # Opening spell exchange: each side casts exactly once, in initiative
    # order, before any physical rounds begin. Intelligence is the magic
    # damage stat (mirrors strength), spirit is the magic accuracy/
    # resistance stat (mirrors dexterity/agility) — reuses the same
    # _hit_chance/DAMAGE_VARIANCE formulas as the physical loop below.
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
            damage = max(
                1, math.floor(attacker_intelligence * SPELL_DAMAGE_MULTIPLIER * rng.uniform(*DAMAGE_VARIANCE))
            )
            if actor == "hero":
                monster_hp = max(0, monster_hp - damage)
            else:
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
            if hit:
                damage = max(1, math.floor(attacker_strength * rng.uniform(*DAMAGE_VARIANCE)))
                if actor == "hero":
                    monster_hp = max(0, monster_hp - damage)
                else:
                    hero_hp = max(0, hero_hp - damage)

            log.append(
                {
                    "round": round_number,
                    "phase": "physical",
                    "actor": actor,
                    "hit": hit,
                    "damage": damage,
                    "defender_hp_remaining": monster_hp if actor == "hero" else hero_hp,
                }
            )

    if monster_hp <= 0:
        victory = True
    elif hero_hp <= 0:
        victory = False
    else:
        # Round cap reached with both sides still standing: higher remaining-HP% wins.
        victory = (hero_hp / hero_max_hp) >= (monster_hp / monster_max_hp)

    xp_awarded = sum(monster_stats.values()) if victory else 0
    gold_awarded = GOLD_PER_VICTORY if victory else 0

    loot: list[dict[str, Any]] = []
    loot_pool = encounter.get("loot_pool") or []
    if victory and loot_pool and rng.random() < DROP_CHANCE:
        chosen = rng.choices(
            loot_pool, weights=[entry["drop_weight"] for entry in loot_pool], k=1
        )[0]
        loot.append(
            {"item_template_slug": chosen["item_template_slug"], "item_name": chosen["item_name"]}
        )

    material_loot: list[dict[str, Any]] = []
    material_pool = encounter.get("material_pool") or []
    if victory and material_pool and rng.random() < MATERIAL_DROP_CHANCE:
        chosen_material = rng.choices(
            material_pool, weights=[entry["drop_weight"] for entry in material_pool], k=1
        )[0]
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
        hero_hp_after=hero_hp,
    )
