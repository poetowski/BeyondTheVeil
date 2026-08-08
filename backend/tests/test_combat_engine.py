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


def _encounter(**overrides):
    encounter = {
        "monster_slug": "veil-wisp",
        "monster_name": "Veil Wisp",
        "monster_stats": dict(MONSTER),
        "loot_pool": [dict(entry) for entry in LOOT_POOL],
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


def test_hero_wins_initiative_ties():
    tied_hero = {**WEAK_HERO, "dexterity": MONSTER["dexterity"], "agility": MONSTER["agility"]}
    result = engine.resolve(
        seed=7, hero_snapshot=tied_hero, hero_base_stats=tied_hero, encounter=_encounter()
    )
    assert result.log[0]["actor"] == "hero"


def test_hit_chance_and_damage_bounds_hold_across_many_seeds():
    for seed in range(200):
        result = engine.resolve(
            seed=seed, hero_snapshot=WEAK_HERO, hero_base_stats=WEAK_HERO, encounter=_encounter()
        )
        for entry in result.log:
            assert entry["actor"] in ("hero", "monster")
            assert isinstance(entry["hit"], bool)
            assert entry["damage"] >= 0
            if entry["hit"]:
                assert entry["damage"] >= 1
            else:
                assert entry["damage"] == 0
            assert entry["defender_hp_remaining"] >= 0


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


def test_round_cap_tie_break_uses_higher_remaining_hp_percentage(monkeypatch):
    monkeypatch.setattr(engine, "MAX_ROUNDS", 1)
    # A single round where both sides survive (very tough monster, weak hero):
    tough_monster = _encounter(
        monster_stats={"strength": 1, "dexterity": 1, "vitality": 1000, "agility": 1, "intelligence": 1, "spirit": 1}
    )
    result = engine.resolve(
        seed=1, hero_snapshot=WEAK_HERO, hero_base_stats=WEAK_HERO, encounter=tough_monster
    )
    # Hero's HP barely dented, monster's HP barely dented relative to its huge pool -> hero should win the %-HP tiebreak.
    assert result.victory is True
