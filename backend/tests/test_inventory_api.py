from app.models.item import EquipmentSlot, ItemInstance, ItemTemplate


def _signup(client, email="inventory@test.com", hero_name="Sable"):
    response = client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": "hunter22", "hero_name": hero_name},
    )
    return response.json()["access_token"]


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


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
    assert by_name["Cracked Helm"]["equipped_slot"] is None
