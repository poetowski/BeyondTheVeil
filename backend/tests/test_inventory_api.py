import uuid

from app.models.item import EquipmentSlot, ItemInstance, ItemTemplate


def _signup(client, email="inventory@test.com", hero_name="Sable"):
    response = client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": "hunter22", "hero_name": hero_name},
    )
    return response.json()["access_token"]


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _hero_id(client, token) -> uuid.UUID:
    me = client.get("/api/v1/users/me", headers=_auth(token)).json()
    return uuid.UUID(me["hero"]["id"])


def test_inventory_requires_auth(client):
    response = client.get("/api/v1/inventory")
    assert response.status_code in (401, 403)


def test_inventory_is_empty_for_a_fresh_hero(client):
    token = _signup(client)

    response = client.get("/api/v1/inventory", headers=_auth(token))

    assert response.status_code == 200
    assert response.json() == []


def test_inventory_lists_equipped_and_unequipped_items(client, db_session):
    token = _signup(client, email="stocked@test.com")

    me = client.get("/api/v1/users/me", headers=_auth(token)).json()
    hero_id = me["hero"]["id"]

    weapon_template = ItemTemplate(
        slug="rusty-dagger", name="Rusty Dagger", slot=EquipmentSlot.WEAPON, base_stats={"strength": 2}
    )
    helmet_template = ItemTemplate(
        slug="cracked-helm", name="Cracked Helm", slot=EquipmentSlot.HELMET, base_stats={"vitality": 1}
    )
    db_session.add_all([weapon_template, helmet_template])
    db_session.flush()

    equipped = ItemInstance(
        template_id=weapon_template.id, owner_hero_id=hero_id, equipped_slot=EquipmentSlot.WEAPON
    )
    unequipped = ItemInstance(template_id=helmet_template.id, owner_hero_id=hero_id, equipped_slot=None)
    db_session.add_all([equipped, unequipped])
    db_session.flush()

    response = client.get("/api/v1/inventory", headers=_auth(token))

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
    by_name = {item["name"]: item for item in body}
    assert by_name["Rusty Dagger"]["equipped_slot"] == "weapon"
    assert by_name["Rusty Dagger"]["slug"] == "rusty-dagger"
    assert by_name["Cracked Helm"]["equipped_slot"] is None
    assert by_name["Cracked Helm"]["slug"] == "cracked-helm"


def test_equip_item_sets_equipped_slot_and_boosts_effective_stats(client, db_session):
    token = _signup(client, email="equip@test.com")
    hero_id = _hero_id(client, token)

    template = ItemTemplate(
        slug="test-equip-sword", name="Test Sword", slot=EquipmentSlot.WEAPON, base_stats={"strength": 3}
    )
    db_session.add(template)
    db_session.flush()
    item = ItemInstance(template_id=template.id, owner_hero_id=hero_id, equipped_slot=None)
    db_session.add(item)
    db_session.flush()

    response = client.post(f"/api/v1/inventory/{item.id}/equip", headers=_auth(token))

    assert response.status_code == 200
    assert response.json()["equipped_slot"] == "weapon"

    me = client.get("/api/v1/users/me", headers=_auth(token)).json()
    assert me["hero"]["bonus_strength"] == 3


def test_equipping_a_second_item_in_the_same_slot_unequips_the_first(client, db_session):
    token = _signup(client, email="swap@test.com")
    hero_id = _hero_id(client, token)

    template = ItemTemplate(
        slug="test-swap-sword", name="Test Sword", slot=EquipmentSlot.WEAPON, base_stats={}
    )
    db_session.add(template)
    db_session.flush()
    first = ItemInstance(template_id=template.id, owner_hero_id=hero_id, equipped_slot=EquipmentSlot.WEAPON)
    second = ItemInstance(template_id=template.id, owner_hero_id=hero_id, equipped_slot=None)
    db_session.add_all([first, second])
    db_session.flush()

    response = client.post(f"/api/v1/inventory/{second.id}/equip", headers=_auth(token))
    assert response.status_code == 200

    inventory = client.get("/api/v1/inventory", headers=_auth(token)).json()
    by_id = {item["id"]: item for item in inventory}
    assert by_id[str(first.id)]["equipped_slot"] is None
    assert by_id[str(second.id)]["equipped_slot"] == "weapon"


def test_unequip_item_clears_equipped_slot(client, db_session):
    token = _signup(client, email="unequip@test.com")
    hero_id = _hero_id(client, token)

    template = ItemTemplate(
        slug="test-unequip-sword", name="Test Sword", slot=EquipmentSlot.WEAPON, base_stats={}
    )
    db_session.add(template)
    db_session.flush()
    item = ItemInstance(template_id=template.id, owner_hero_id=hero_id, equipped_slot=EquipmentSlot.WEAPON)
    db_session.add(item)
    db_session.flush()

    response = client.post(f"/api/v1/inventory/{item.id}/unequip", headers=_auth(token))

    assert response.status_code == 200
    assert response.json()["equipped_slot"] is None


def test_equip_of_unowned_item_is_rejected(client, db_session):
    owner_token = _signup(client, email="equip-owner@test.com", hero_name="Owner")
    owner_hero_id = _hero_id(client, owner_token)
    intruder_token = _signup(client, email="equip-intruder@test.com", hero_name="Intruder")

    template = ItemTemplate(
        slug="test-guarded-sword", name="Test Sword", slot=EquipmentSlot.WEAPON, base_stats={}
    )
    db_session.add(template)
    db_session.flush()
    item = ItemInstance(template_id=template.id, owner_hero_id=owner_hero_id, equipped_slot=None)
    db_session.add(item)
    db_session.flush()

    response = client.post(f"/api/v1/inventory/{item.id}/equip", headers=_auth(intruder_token))
    assert response.status_code == 403


def test_equip_of_nonexistent_item_returns_404(client):
    token = _signup(client, email="equip-missing@test.com")
    response = client.post(f"/api/v1/inventory/{uuid.uuid4()}/equip", headers=_auth(token))
    assert response.status_code == 404


def test_equip_below_level_requirement_is_rejected(client, db_session):
    token = _signup(client, email="equip-level@test.com")
    hero_id = _hero_id(client, token)

    template = ItemTemplate(
        slug="test-high-level-sword",
        name="Test Sword",
        slot=EquipmentSlot.WEAPON,
        base_stats={},
        level_requirement=5,
    )
    db_session.add(template)
    db_session.flush()
    item = ItemInstance(template_id=template.id, owner_hero_id=hero_id, equipped_slot=None)
    db_session.add(item)
    db_session.flush()

    response = client.post(f"/api/v1/inventory/{item.id}/equip", headers=_auth(token))
    assert response.status_code == 409
