from app.models.hero import Hero
from app.models.item import EquipmentSlot, ItemInstance, ItemTemplate
from app.services import hero_service


def test_compute_effective_stats_sums_equipped_item_bonuses():
    hero = Hero(
        strength=5, dexterity=5, vitality=5, agility=5, intelligence=5, spirit=5
    )
    weapon_template = ItemTemplate(
        slug="sword", name="Sword", slot=EquipmentSlot.WEAPON, base_stats={"strength": 3}
    )
    weapon = ItemInstance(
        equipped_slot=EquipmentSlot.WEAPON, rolled_stats={"strength": 1}
    )
    weapon.template = weapon_template

    unequipped_template = ItemTemplate(
        slug="spare-helmet", name="Spare Helmet", slot=EquipmentSlot.HELMET, base_stats={"vitality": 100}
    )
    unequipped = ItemInstance(equipped_slot=None)
    unequipped.template = unequipped_template

    effective = hero_service.compute_effective_stats(hero, [weapon, unequipped])

    assert effective["strength"] == 5 + 3 + 1
    assert effective["vitality"] == 5, "unequipped items must not contribute stats"
    assert effective["dexterity"] == 5


def test_base_plus_bonus_equals_effective_for_every_stat():
    hero = Hero(strength=10, dexterity=10, vitality=10, agility=10, intelligence=10, spirit=10)
    template = ItemTemplate(
        slug="sword", name="Sword", slot=EquipmentSlot.WEAPON, base_stats={"strength": 3}
    )
    weapon = ItemInstance(equipped_slot=EquipmentSlot.WEAPON, rolled_stats={"strength": 1})
    weapon.template = template

    base = hero_service.compute_base_stats(hero)
    bonus = hero_service.compute_stat_bonuses(hero, [weapon])
    effective = hero_service.compute_effective_stats(hero, [weapon])

    for stat in hero_service.STAT_NAMES:
        assert base[stat] + bonus[stat] == effective[stat]
    assert bonus["strength"] == 4
    assert bonus["vitality"] == 0


def test_compute_max_hp_derives_from_effective_vitality():
    assert hero_service.compute_max_hp(0) == hero_service.BASE_HP
    assert (
        hero_service.compute_max_hp(10)
        == hero_service.BASE_HP + 10 * hero_service.HP_PER_VITALITY
    )


def test_xp_required_for_level_uses_the_steeper_curve():
    assert hero_service.xp_required_for_level(1) == 100
    assert hero_service.xp_required_for_level(2) == round(2**1.5 * 100)


def test_apply_xp_below_threshold_does_not_level_up():
    hero = Hero(level=1, xp=0)
    levels_gained = hero_service.apply_xp(hero, 50)
    assert levels_gained == 0
    assert hero.level == 1
    assert hero.xp == 50


def test_apply_xp_exactly_at_threshold_levels_up_and_resets_progress():
    hero = Hero(level=1, xp=0)
    levels_gained = hero_service.apply_xp(hero, 100)
    assert levels_gained == 1
    assert hero.level == 2
    assert hero.xp == 0


def test_apply_xp_can_cause_multiple_level_ups_at_once():
    hero = Hero(level=1, xp=0)
    # 100 to hit level 2, then round(2**1.5*100)=283 to hit level 3.
    levels_gained = hero_service.apply_xp(hero, 100 + 283)
    assert levels_gained == 2
    assert hero.level == 3
    assert hero.xp == 0


def test_leveling_does_not_change_base_stats():
    hero = Hero(
        level=1, xp=0, strength=10, dexterity=10, intelligence=10, vitality=10, agility=10, spirit=10
    )
    hero_service.apply_xp(hero, 100)
    for stat in hero_service.STAT_NAMES:
        assert getattr(hero, stat) == 10, "level is a pure content gate, not a stat source"


def test_train_stat_cost_at_baseline_is_the_base_cost():
    base = hero_service.BASELINE_STAT_VALUE
    assert hero_service.train_stat_cost(base) == hero_service.TRAIN_STAT_BASE_COST


def test_train_stat_cost_follows_the_power_curve_above_baseline():
    base = hero_service.BASELINE_STAT_VALUE
    assert hero_service.train_stat_cost(base + 1) == round(
        hero_service.TRAIN_STAT_BASE_COST * 2**hero_service.TRAIN_STAT_EXPONENT
    )
    assert hero_service.train_stat_cost(base + 4) == round(
        hero_service.TRAIN_STAT_BASE_COST * 5**hero_service.TRAIN_STAT_EXPONENT
    )


def test_train_stat_cost_grows_steeply_not_linearly():
    base = hero_service.BASELINE_STAT_VALUE
    first_step = hero_service.train_stat_cost(base + 1) - hero_service.train_stat_cost(base)
    later_step = hero_service.train_stat_cost(base + 5) - hero_service.train_stat_cost(base + 4)
    assert later_step > first_step, "each successive point should cost more than the last"


def test_train_stat_spends_gold_and_increments_the_stat(db_session, hero_factory):
    hero = hero_factory(gold=100, strength=10)

    hero_service.train_stat(db_session, hero, "strength")

    assert hero.strength == 11
    assert hero.gold == 100 - hero_service.TRAIN_STAT_BASE_COST


def test_train_stat_without_enough_gold_raises(db_session, hero_factory):
    hero = hero_factory(gold=0, strength=10)

    try:
        hero_service.train_stat(db_session, hero, "strength")
        assert False, "expected InsufficientGoldError"
    except hero_service.InsufficientGoldError:
        pass
    assert hero.strength == 10


def test_train_stat_rejects_an_unknown_stat_name(db_session, hero_factory):
    hero = hero_factory(gold=100)

    try:
        hero_service.train_stat(db_session, hero, "luck")
        assert False, "expected UnknownStatError"
    except hero_service.UnknownStatError:
        pass
