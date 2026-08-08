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
