import uuid
from datetime import datetime, timedelta, timezone

from app.models.item import EquipmentSlot, ItemTemplate
from app.models.veil_run import VeilRun, VeilRunStatus


def _signup(client, email="veil@test.com", hero_name="Bramble"):
    response = client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": "hunter22", "hero_name": hero_name},
    )
    return response.json()["access_token"]


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_enter_veil_requires_auth(client):
    response = client.post("/api/v1/veil/enter")
    assert response.status_code in (401, 403)


def test_enter_veil_creates_hidden_in_progress_run(client):
    token = _signup(client)

    response = client.post("/api/v1/veil/enter", headers=_auth(token))

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "in_progress"
    assert body["result"] is None
    assert body["resolves_at"] > body["started_at"]


def test_enter_veil_is_idempotent(client):
    token = _signup(client)

    first = client.post("/api/v1/veil/enter", headers=_auth(token)).json()
    second = client.post("/api/v1/veil/enter", headers=_auth(token)).json()

    assert first["id"] == second["id"]


def test_active_run_is_null_when_none_started(client):
    token = _signup(client)

    response = client.get("/api/v1/veil/active", headers=_auth(token))

    assert response.status_code == 200
    assert response.json() is None


def test_active_run_returns_the_in_progress_run(client):
    token = _signup(client)
    entered = client.post("/api/v1/veil/enter", headers=_auth(token)).json()

    active = client.get("/api/v1/veil/active", headers=_auth(token)).json()

    assert active["id"] == entered["id"]
    assert active["result"] is None


def test_claim_before_resolves_at_stays_hidden(client):
    token = _signup(client)
    entered = client.post("/api/v1/veil/enter", headers=_auth(token)).json()

    claimed = client.post(f"/api/v1/veil/{entered['id']}/claim", headers=_auth(token)).json()

    assert claimed["status"] == "in_progress"
    assert claimed["result"] is None


def test_claim_after_resolves_at_reveals_result_and_credits_xp(client, db_session):
    token = _signup(client, email="claimer@test.com")
    entered = client.post("/api/v1/veil/enter", headers=_auth(token)).json()

    run = db_session.get(VeilRun, entered["id"])
    run.resolves_at = run.started_at + timedelta(milliseconds=1)
    db_session.flush()

    claimed = client.post(f"/api/v1/veil/{entered['id']}/claim", headers=_auth(token)).json()

    assert claimed["status"] == "completed"
    assert claimed["result"] is not None
    assert "xp_awarded" in claimed["result"]

    me = client.get("/api/v1/users/me", headers=_auth(token)).json()
    assert me["hero"]["xp"] == claimed["result"]["xp_awarded"]


def test_active_run_reveals_result_before_explicit_claim(client, db_session):
    token = _signup(client, email="reveal@test.com")
    entered = client.post("/api/v1/veil/enter", headers=_auth(token)).json()

    run = db_session.get(VeilRun, entered["id"])
    run.resolves_at = run.started_at + timedelta(milliseconds=1)
    db_session.flush()

    active = client.get("/api/v1/veil/active", headers=_auth(token)).json()

    assert active["status"] == "in_progress", "reveal happens before the claim finalizes it"
    assert active["result"] is not None


def test_claim_of_another_users_run_is_rejected(client):
    owner_token = _signup(client, email="owner@test.com", hero_name="Owner")
    entered = client.post("/api/v1/veil/enter", headers=_auth(owner_token)).json()

    intruder_token = _signup(client, email="intruder@test.com", hero_name="Intruder")
    response = client.post(f"/api/v1/veil/{entered['id']}/claim", headers=_auth(intruder_token))

    assert response.status_code == 404


def test_claim_of_nonexistent_run_is_rejected(client):
    token = _signup(client, email="ghost@test.com")

    response = client.post(
        "/api/v1/veil/00000000-0000-0000-0000-000000000000/claim", headers=_auth(token)
    )

    assert response.status_code == 404


def test_claiming_loot_materializes_an_item_instance_in_the_backpack(client, db_session):
    token = _signup(client, email="looter@test.com")
    me = client.get("/api/v1/users/me", headers=_auth(token)).json()
    hero_id = me["hero"]["id"]

    template = ItemTemplate(
        slug="test-loot-sword", name="Test Loot Sword", slot=EquipmentSlot.WEAPON, base_stats={}
    )
    db_session.add(template)
    db_session.flush()

    now = datetime.now(timezone.utc)
    run = VeilRun(
        hero_id=uuid.UUID(hero_id),
        seed=1,
        status=VeilRunStatus.IN_PROGRESS,
        started_at=now - timedelta(seconds=10),
        duration_seconds=5,
        resolves_at=now - timedelta(seconds=5),
        result_payload={
            "victory": True,
            "monster_name": "Test Monster",
            "log": [],
            "loot": [{"item_template_slug": "test-loot-sword", "item_name": "Test Loot Sword"}],
            "xp_awarded": 5,
        },
    )
    db_session.add(run)
    db_session.commit()

    claimed = client.post(f"/api/v1/veil/{run.id}/claim", headers=_auth(token)).json()
    assert claimed["status"] == "completed"

    inventory = client.get("/api/v1/inventory", headers=_auth(token)).json()
    assert len(inventory) == 1
    assert inventory[0]["name"] == "Test Loot Sword"
    assert inventory[0]["equipped_slot"] is None
