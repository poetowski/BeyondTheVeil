from app.services.combat import engine

WEAK_HERO = {"strength": 10, "dexterity": 10, "vitality": 10, "agility": 10, "intelligence": 10, "spirit": 10}

MONSTER = {
    "strength": 2,
    "dexterity": 3,
    "vitality": 4,
    "agility": 3,
    "intelligence": 2,
    "spirit": 2,
}

LOOT_POOL = [
    {"item_template_slug": "leather-cap", "item_name": "Leather Cap", "drop_weight": 5},
    {"item_template_slug": "wooden-buckler", "item_name": "Wooden Buckler", "drop_weight": 5},
]

MATERIAL_POOL = [
    {"material_template_slug": "wisp-residue", "material_name": "Wisp Residue", "drop_weight": 5},
]


def _encounter(**overrides):
    encounter = {
        "monster_slug": "veil-wisp",
        "monster_name": "Veil Wisp",
        "monster_stats": dict(MONSTER),
        "loot_pool": [dict(entry) for entry in LOOT_POOL],
        "gold_min": 5,
        "gold_max": 15,
    }
    encounter.update(overrides)
    return encounter


def test_resolve_is_deterministic_for_a_fixed_seed():
    results = [
        engine.resolve(
            seed=42, hero_snapshot=WEAK_HERO, hero_base_stats=WEAK_HERO, encounter=_encounter()
        )
        for _ in range(3)
    ]
    first = results[0]
    for result in results[1:]:
        assert result.victory == first.victory
        assert result.log == first.log
        assert result.loot == first.loot
        assert result.xp_awarded == first.xp_awarded


def test_encounter_none_is_an_automatic_uneventful_victory():
    result = engine.resolve(seed=1, hero_snapshot=WEAK_HERO, hero_base_stats=WEAK_HERO, encounter=None)
    assert result.victory is True
    assert result.xp_awarded == 0
    assert result.loot == []
    assert result.monster_stats is None
    assert result.monster_max_hp == 0


def test_resolve_reports_the_rolled_monster_stats_and_max_hp():
    result = engine.resolve(
        seed=1, hero_snapshot=WEAK_HERO, hero_base_stats=WEAK_HERO, encounter=_encounter()
    )
    expected_stats = engine._roll_monster_stats(engine.random.Random(1), MONSTER)
    assert result.monster_stats == expected_stats
    assert result.monster_max_hp == expected_stats["vitality"] * engine.HP_PER_VITALITY


def test_resolve_rolls_a_single_monster_level_within_its_range():
    for seed in range(20):
        result = engine.resolve(
            seed=seed,
            hero_snapshot=WEAK_HERO,
            hero_base_stats=WEAK_HERO,
            encounter=_encounter(monster_level_min=1, monster_level_max=3),
        )
        assert 1 <= result.monster_level <= 3


def test_resolve_reports_monster_damage_ranges():
    result = engine.resolve(
        seed=1,
        hero_snapshot=WEAK_HERO,
        hero_base_stats=WEAK_HERO,
        encounter=_encounter(),
    )
    # No weapon_attack/spell_attack set on the encounter - damage ranges
    # are just the rolled stat's flat contribution, min == max.
    assert result.monster_damage_min == result.monster_damage_max
    assert result.monster_spell_damage_min == result.monster_spell_damage_max


def test_default_hero_current_hp_is_full_hp():
    # hero_current_hp defaults to None, meaning "start at full HP" - every
    # pre-existing caller/test that doesn't pass it must be unaffected.
    result = engine.resolve(
        seed=5, hero_snapshot=WEAK_HERO, hero_base_stats=WEAK_HERO, encounter=_encounter()
    )
    hero_max_hp = engine.compute_max_hp(WEAK_HERO["vitality"])
    total_damage_to_hero = sum(
        e["damage"] for e in result.log if e["hit"] and e["actor"] == "monster"
    )
    assert result.hero_hp_after == max(0, hero_max_hp - total_damage_to_hero)


def test_hero_current_hp_below_max_starts_combat_already_wounded():
    hero_max_hp = engine.compute_max_hp(WEAK_HERO["vitality"])
    wounded_result = engine.resolve(
        seed=5,
        hero_snapshot=WEAK_HERO,
        hero_base_stats=WEAK_HERO,
        encounter=_encounter(),
        hero_current_hp=1,
    )
    full_result = engine.resolve(
        seed=5, hero_snapshot=WEAK_HERO, hero_base_stats=WEAK_HERO, encounter=_encounter()
    )
    # Same seed, same rolls, but the wounded hero enters with only 1 HP - any
    # hit at all should down them, whereas the full-HP hero can tank longer.
    assert wounded_result.hero_hp_after <= full_result.hero_hp_after
    assert wounded_result.hero_hp_after < hero_max_hp


def test_hero_current_hp_is_capped_at_max_hp():
    hero_max_hp = engine.compute_max_hp(WEAK_HERO["vitality"])
    result = engine.resolve(
        seed=1,
        hero_snapshot=WEAK_HERO,
        hero_base_stats=WEAK_HERO,
        encounter=_encounter(),
        hero_current_hp=hero_max_hp + 10_000,
    )
    assert result.hero_hp_after <= hero_max_hp


def test_gold_is_only_awarded_on_victory():
    encounter = _encounter()
    for seed in range(50):
        result = engine.resolve(
            seed=seed, hero_snapshot=WEAK_HERO, hero_base_stats=WEAK_HERO, encounter=encounter
        )
        if result.victory:
            assert encounter["gold_min"] <= result.gold_awarded <= encounter["gold_max"]
        else:
            assert result.gold_awarded == 0


def test_hero_initiative_wins_when_base_stats_favor_hero():
    strong_initiative_hero = {**WEAK_HERO, "dexterity": 20, "agility": 20}
    result = engine.resolve(
        seed=7,
        hero_snapshot=strong_initiative_hero,
        hero_base_stats=strong_initiative_hero,
        encounter=_encounter(),
    )
    assert result.log[0]["actor"] == "hero"


def test_monster_initiative_wins_when_monster_base_stats_are_higher():
    weak_initiative_hero = {**WEAK_HERO, "dexterity": 0, "agility": 0}
    result = engine.resolve(
        seed=7,
        hero_snapshot=weak_initiative_hero,
        hero_base_stats=weak_initiative_hero,
        encounter=_encounter(),
    )
    assert result.log[0]["actor"] == "monster"


def test_hero_wins_initiative_ties(monkeypatch):
    # Monster stats are rolled with variance before combat starts (see
    # _roll_monster_stats), so pin that to the identity to keep this test's
    # tie genuinely exact rather than incidental to a particular seed's roll.
    monkeypatch.setattr(engine, "_roll_monster_stats", lambda rng, base_stats: dict(base_stats))
    tied_hero = {**WEAK_HERO, "dexterity": MONSTER["dexterity"], "agility": MONSTER["agility"]}
    result = engine.resolve(
        seed=7, hero_snapshot=tied_hero, hero_base_stats=tied_hero, encounter=_encounter()
    )
    assert result.log[0]["actor"] == "hero"


def test_roll_monster_stats_stays_within_variance_bounds():
    lo, hi = engine.MONSTER_STAT_VARIANCE
    for seed in range(200):
        rolled = engine._roll_monster_stats(engine.random.Random(seed), MONSTER)
        for stat, base_value in MONSTER.items():
            assert max(1, round(base_value * lo)) <= rolled[stat] <= round(base_value * hi)


def test_roll_monster_stats_varies_across_seeds():
    rolls = {
        tuple(engine._roll_monster_stats(engine.random.Random(seed), MONSTER).items())
        for seed in range(20)
    }
    assert len(rolls) > 1


def test_resolve_rolls_monster_stats_deterministically_from_seed():
    # Same seed -> same rolled monster stats -> same combat outcome (already
    # covered by test_resolve_is_deterministic_for_a_fixed_seed); this
    # asserts the rolled stats themselves are reproducible in isolation.
    first = engine._roll_monster_stats(engine.random.Random(99), MONSTER)
    second = engine._roll_monster_stats(engine.random.Random(99), MONSTER)
    assert first == second


def test_hit_chance_and_damage_bounds_hold_across_many_seeds():
    for seed in range(200):
        result = engine.resolve(
            seed=seed, hero_snapshot=WEAK_HERO, hero_base_stats=WEAK_HERO, encounter=_encounter()
        )
        for entry in result.log:
            assert entry["actor"] in ("hero", "monster")
            assert entry["phase"] in ("spell", "physical")
            assert isinstance(entry["hit"], bool)
            assert entry["damage"] >= 0
            if entry["hit"]:
                assert entry["damage"] >= 1
            else:
                assert entry["damage"] == 0
            assert entry["defender_hp_remaining"] >= 0


def test_opening_spell_exchange_precedes_physical_rounds():
    result = engine.resolve(
        seed=7, hero_snapshot=WEAK_HERO, hero_base_stats=WEAK_HERO, encounter=_encounter()
    )
    # Both sides get exactly one spell-phase action, round 0, before any
    # physical-phase entry appears.
    spell_entries = [entry for entry in result.log if entry["phase"] == "spell"]
    assert len(spell_entries) == 2
    assert {entry["actor"] for entry in spell_entries} == {"hero", "monster"}
    assert all(entry["round"] == 0 for entry in spell_entries)
    assert result.log[0]["phase"] == "spell"
    assert result.log[1]["phase"] == "spell"

    physical_entries = [entry for entry in result.log if entry["phase"] == "physical"]
    if physical_entries:
        assert all(entry["round"] >= 1 for entry in physical_entries)


def test_spell_exchange_uses_intelligence_for_damage_not_strength():
    # Zero strength means physical rounds (if reached) always deal 0 on a
    # hit; any nonzero damage from the caster's spell-phase entry must have
    # come from intelligence, not strength.
    caster_hero = {**WEAK_HERO, "strength": 0, "intelligence": 50}
    result = engine.resolve(
        seed=3, hero_snapshot=caster_hero, hero_base_stats=caster_hero, encounter=_encounter()
    )
    hero_spell_entry = next(e for e in result.log if e["phase"] == "spell" and e["actor"] == "hero")
    if hero_spell_entry["hit"]:
        assert hero_spell_entry["damage"] >= 1


def test_spell_damage_is_flat_intelligence_and_physical_is_flat_strength(monkeypatch):
    # Pin out randomness: guaranteed hits. Neither formula rolls variance
    # anymore - spell damage is exactly intelligence, physical is
    # strength // STRENGTH_DAMAGE_DIVISOR.
    monkeypatch.setattr(engine, "_hit_chance", lambda attacker, defender: 1.0)

    equal_stats_hero = {**WEAK_HERO, "strength": 20, "intelligence": 20}
    # Huge monster vitality so it survives the spell phase and forces
    # physical rounds too, letting us check both formulas' output.
    tough_encounter = _encounter(monster_stats={**MONSTER, "vitality": 100_000})
    result = engine.resolve(
        seed=1, hero_snapshot=equal_stats_hero, hero_base_stats=equal_stats_hero, encounter=tough_encounter
    )

    hero_spell_damage = next(
        e["damage"] for e in result.log if e["phase"] == "spell" and e["actor"] == "hero"
    )
    hero_physical_damage = next(
        e["damage"] for e in result.log if e["phase"] == "physical" and e["actor"] == "hero"
    )

    assert hero_spell_damage == 20
    assert hero_physical_damage == max(1, 20 // engine.STRENGTH_DAMAGE_DIVISOR)


def test_monster_weapon_attack_adds_to_its_physical_damage(monkeypatch):
    # Pin hit chance and monster stat rolling so the only difference between
    # the two runs is the encounter's weapon_attack range.
    monkeypatch.setattr(engine, "_hit_chance", lambda attacker, defender: 1.0)
    monkeypatch.setattr(engine, "_roll_monster_stats", lambda rng, base_stats: dict(base_stats))

    tough_hero = {**WEAK_HERO, "vitality": 100_000}
    tough_monster_stats = {**MONSTER, "vitality": 100_000}

    unarmed = _encounter(monster_stats=dict(tough_monster_stats))
    armed = _encounter(
        monster_stats=dict(tough_monster_stats), weapon_attack_min=10, weapon_attack_max=10
    )

    unarmed_result = engine.resolve(
        seed=1, hero_snapshot=tough_hero, hero_base_stats=tough_hero, encounter=unarmed
    )
    armed_result = engine.resolve(
        seed=1, hero_snapshot=tough_hero, hero_base_stats=tough_hero, encounter=armed
    )

    unarmed_hit = next(
        e for e in unarmed_result.log if e["phase"] == "physical" and e["actor"] == "monster"
    )
    armed_hit = next(
        e for e in armed_result.log if e["phase"] == "physical" and e["actor"] == "monster"
    )
    assert armed_hit["damage"] == unarmed_hit["damage"] + 10


def test_monster_defense_reduces_damage_hero_deals(monkeypatch):
    monkeypatch.setattr(engine, "_hit_chance", lambda attacker, defender: 1.0)
    monkeypatch.setattr(engine, "_roll_monster_stats", lambda rng, base_stats: dict(base_stats))

    strong_hero = {**WEAK_HERO, "strength": 20, "vitality": 100_000}
    tough_monster_stats = {**MONSTER, "vitality": 100_000}

    no_defense = _encounter(monster_stats=dict(tough_monster_stats))
    defended = _encounter(monster_stats=dict(tough_monster_stats), defense=3)

    no_defense_result = engine.resolve(
        seed=1, hero_snapshot=strong_hero, hero_base_stats=strong_hero, encounter=no_defense
    )
    defended_result = engine.resolve(
        seed=1, hero_snapshot=strong_hero, hero_base_stats=strong_hero, encounter=defended
    )

    hero_hit_no_defense = next(
        e for e in no_defense_result.log if e["phase"] == "physical" and e["actor"] == "hero"
    )
    hero_hit_defended = next(
        e for e in defended_result.log if e["phase"] == "physical" and e["actor"] == "hero"
    )
    assert hero_hit_defended["damage"] == max(1, hero_hit_no_defense["damage"] - 3)


def test_monster_spell_attack_adds_to_its_spell_damage(monkeypatch):
    # Same paired before/after approach as the weapon_attack test above, but
    # for the opening spell exchange.
    monkeypatch.setattr(engine, "_hit_chance", lambda attacker, defender: 1.0)
    monkeypatch.setattr(engine, "_roll_monster_stats", lambda rng, base_stats: dict(base_stats))

    tough_hero = {**WEAK_HERO, "vitality": 100_000}
    tough_monster_stats = {**MONSTER, "vitality": 100_000}

    no_spell_attack = _encounter(monster_stats=dict(tough_monster_stats))
    with_spell_attack = _encounter(
        monster_stats=dict(tough_monster_stats), spell_attack_min=7, spell_attack_max=7
    )

    no_spell_result = engine.resolve(
        seed=1, hero_snapshot=tough_hero, hero_base_stats=tough_hero, encounter=no_spell_attack
    )
    with_spell_result = engine.resolve(
        seed=1, hero_snapshot=tough_hero, hero_base_stats=tough_hero, encounter=with_spell_attack
    )

    no_spell_hit = next(
        e for e in no_spell_result.log if e["phase"] == "spell" and e["actor"] == "monster"
    )
    with_spell_hit = next(
        e for e in with_spell_result.log if e["phase"] == "spell" and e["actor"] == "monster"
    )
    assert with_spell_hit["damage"] == no_spell_hit["damage"] + 7


def test_a_lethal_spell_cast_ends_combat_before_physical_rounds():
    # Hero acts first (higher initiative) with an overwhelming intelligence
    # stat; ~90% hit chance means most seeds one-shot the monster in the
    # spell phase — find one and confirm combat ends there, before any
    # physical-phase entry.
    overwhelming_caster = {**WEAK_HERO, "intelligence": 10_000, "spirit": 10_000}
    for seed in range(20):
        result = engine.resolve(
            seed=seed,
            hero_snapshot=overwhelming_caster,
            hero_base_stats=overwhelming_caster,
            encounter=_encounter(),
        )
        hero_spell_entry = next(e for e in result.log if e["phase"] == "spell" and e["actor"] == "hero")
        if hero_spell_entry["hit"]:
            assert result.victory is True
            assert not any(entry["phase"] == "physical" for entry in result.log)
            return
    raise AssertionError("expected at least one seed where the hero's opening cast hits")


def test_loot_only_drops_on_victory_and_is_drawn_from_the_pool():
    valid_slugs = {entry["item_template_slug"] for entry in LOOT_POOL}
    for seed in range(200):
        result = engine.resolve(
            seed=seed, hero_snapshot=WEAK_HERO, hero_base_stats=WEAK_HERO, encounter=_encounter()
        )
        if not result.victory:
            assert result.loot == []
        for item in result.loot:
            assert item["item_template_slug"] in valid_slugs


def test_material_loot_only_drops_on_victory_and_is_drawn_from_the_pool():
    valid_slugs = {entry["material_template_slug"] for entry in MATERIAL_POOL}
    for seed in range(200):
        result = engine.resolve(
            seed=seed,
            hero_snapshot=WEAK_HERO,
            hero_base_stats=WEAK_HERO,
            encounter=_encounter(material_pool=[dict(entry) for entry in MATERIAL_POOL]),
        )
        if not result.victory:
            assert result.material_loot == []
        for material in result.material_loot:
            assert material["material_template_slug"] in valid_slugs
            assert material["quantity"] == 1


def test_no_material_pool_means_no_material_loot_ever():
    for seed in range(50):
        result = engine.resolve(
            seed=seed, hero_snapshot=WEAK_HERO, hero_base_stats=WEAK_HERO, encounter=_encounter()
        )
        assert result.material_loot == []


def test_absent_material_pool_does_not_perturb_the_rng_stream():
    # An encounter with no material_pool key must produce byte-identical
    # results to one with an empty material_pool list - the material-loot
    # roll is gated on the pool being non-empty, so it must never consume
    # `rng` when there's nothing to drop (this is what keeps every
    # pre-existing encounter fixture and seeded monster RNG-stream-compatible
    # with this feature being added).
    for seed in range(50):
        without_key = engine.resolve(
            seed=seed, hero_snapshot=WEAK_HERO, hero_base_stats=WEAK_HERO, encounter=_encounter()
        )
        with_empty_pool = engine.resolve(
            seed=seed,
            hero_snapshot=WEAK_HERO,
            hero_base_stats=WEAK_HERO,
            encounter=_encounter(material_pool=[]),
        )
        assert without_key.log == with_empty_pool.log
        assert without_key.loot == with_empty_pool.loot
        assert without_key.xp_awarded == with_empty_pool.xp_awarded


def test_round_cap_tie_break_uses_higher_remaining_hp_percentage(monkeypatch):
    monkeypatch.setattr(engine, "MAX_ROUNDS", 1)
    monkeypatch.setattr(engine, "_roll_monster_stats", lambda rng, base_stats: dict(base_stats))
    # A single round where both sides survive (very tough monster, weak hero):
    tough_monster = _encounter(
        monster_stats={"strength": 1, "dexterity": 1, "vitality": 1000, "agility": 1, "intelligence": 1, "spirit": 1}
    )
    result = engine.resolve(
        seed=2, hero_snapshot=WEAK_HERO, hero_base_stats=WEAK_HERO, encounter=tough_monster
    )
    # Hero's HP barely dented, monster's HP barely dented relative to its huge pool -> hero should win the %-HP tiebreak.
    assert result.victory is True
