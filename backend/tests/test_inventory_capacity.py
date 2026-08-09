import uuid
from datetime import datetime, timedelta, timezone

from app.models.hero import Hero
from app.models.item import EquipmentSlot, ItemInstance, ItemTemplate
from app.models.veil_run import VeilRun, VeilRunStatus


def _signup(client, email="capacity@test.com", hero_name="Thistle"):
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


def _make_claimable_run(hero_id: uuid.UUID, item_slug: str) -> VeilRun:
    now = datetime.now(timezone.utc)
    return VeilRun(
        hero_id=hero_id,
        seed=1,
        status=VeilRunStatus.IN_PROGRESS,
        started_at=now - timedelta(seconds=10),
        duration_seconds=5,
        resolves_at=now - timedelta(seconds=5),
        result_payload={
            "victory": True,
            "monster_name": "Test Monster",
            "log": [],
            "loot": [{"item_template_slug": item_slug, "item_name": "Capacity Sword"}],
            "xp_awarded": 5,
        },
    )


def test_loot_is_skipped_when_backpack_is_full(client, db_session):
    token = _signup(client, email="full@test.com")
    hero_id = _hero_id(client, token)

    hero = db_session.get(Hero, hero_id)
    hero.inventory_capacity = 1
    db_session.flush()

    template = ItemTemplate(
        slug="capacity-blocking-item", name="Blocker", slot=EquipmentSlot.HELMET, base_stats={}
    )
    db_session.add(template)
    db_session.flush()
    db_session.add(ItemInstance(template_id=template.id, owner_hero_id=hero_id, equipped_slot=None))
    db_session.flush()

    loot_template = ItemTemplate(
        slug="capacity-loot-sword", name="Capacity Sword", slot=EquipmentSlot.WEAPON, base_stats={}
    )
    db_session.add(loot_template)
    db_session.flush()

    run = _make_claimable_run(hero_id, "capacity-loot-sword")
    db_session.add(run)
    db_session.commit()

    claimed = client.post(f"/api/v1/veil/{run.id}/claim", headers=_auth(token)).json()

    assert claimed["status"] == "completed"
    assert claimed["result"]["loot_skipped"] == [
        {"item_template_slug": "capacity-loot-sword", "item_name": "Capacity Sword"}
    ]

    inventory = client.get("/api/v1/inventory", headers=_auth(token)).json()
    assert len(inventory) == 1, "the loot item must not have been added once the backpack was full"
    assert inventory[0]["name"] == "Blocker"


def test_loot_is_added_when_capacity_available(client, db_session):
    token = _signup(client, email="roomy@test.com")
    hero_id = _hero_id(client, token)

    template = ItemTemplate(
        slug="capacity-roomy-sword", name="Roomy Sword", slot=EquipmentSlot.WEAPON, base_stats={}
    )
    db_session.add(template)
    db_session.flush()

    run = _make_claimable_run(hero_id, "capacity-roomy-sword")
    db_session.add(run)
    db_session.commit()

    claimed = client.post(f"/api/v1/veil/{run.id}/claim", headers=_auth(token)).json()

    assert claimed["result"]["loot_skipped"] == []
    inventory = client.get("/api/v1/inventory", headers=_auth(token)).json()
    assert len(inventory) == 1
    assert inventory[0]["name"] == "Roomy Sword"
