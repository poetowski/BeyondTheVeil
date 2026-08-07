from sqlalchemy.exc import IntegrityError

from app.models.item import EquipmentSlot, ItemInstance, ItemTemplate


def _make_template(db_session, slug: str, slot: EquipmentSlot) -> ItemTemplate:
    template = ItemTemplate(slug=slug, name=slug, slot=slot, base_stats={})
    db_session.add(template)
    db_session.flush()
    return template


def test_two_items_cannot_occupy_the_same_slot(db_session, hero_factory):
    hero = hero_factory()
    template = _make_template(db_session, "iron-sword", EquipmentSlot.WEAPON)

    db_session.add(
        ItemInstance(template_id=template.id, owner_hero_id=hero.id, equipped_slot=EquipmentSlot.WEAPON)
    )
    db_session.flush()

    db_session.add(
        ItemInstance(template_id=template.id, owner_hero_id=hero.id, equipped_slot=EquipmentSlot.WEAPON)
    )
    try:
        db_session.flush()
        assert False, "expected IntegrityError from uq_hero_equipped_slot"
    except IntegrityError:
        db_session.rollback()


def test_unequipped_items_are_unlimited(db_session, hero_factory):
    hero = hero_factory()
    template = _make_template(db_session, "spare-sword", EquipmentSlot.WEAPON)

    db_session.add_all(
        [
            ItemInstance(template_id=template.id, owner_hero_id=hero.id, equipped_slot=None)
            for _ in range(3)
        ]
    )
    db_session.flush()  # should not raise


def test_equipped_slot_requires_an_owner(db_session):
    template = ItemTemplate(slug="orphan-sword", name="orphan", slot=EquipmentSlot.WEAPON, base_stats={})
    db_session.add(template)
    db_session.flush()

    db_session.add(
        ItemInstance(template_id=template.id, owner_hero_id=None, equipped_slot=EquipmentSlot.WEAPON)
    )
    try:
        db_session.flush()
        assert False, "expected CheckConstraint violation: equipped item needs an owner"
    except IntegrityError:
        db_session.rollback()
