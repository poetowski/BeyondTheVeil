import uuid
from datetime import datetime, timedelta, timezone

from app.models.campaign import CampaignNode
from app.models.hero import Hero
from app.models.monster import MonsterTemplate
from app.models.veil_run import VeilRun, VeilRunStatus


def _signup(client, email="campaign@test.com", hero_name="Rowan"):
    response = client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": "hunter22", "hero_name": hero_name},
    )
    return response.json()["access_token"]


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _make_node(db_session, *, slug, order_index, required_level=1, gold_cost=0):
    monster = MonsterTemplate(
        slug=f"{slug}-monster",
        name=f"{slug} Monster",
        level_range_min=1,
        level_range_max=99,
        base_stats={
            "strength": 1,
            "dexterity": 1,
            "vitality": 1,
            "agility": 1,
            "intelligence": 1,
            "spirit": 1,
        },
    )
    db_session.add(monster)
    db_session.flush()
    node = CampaignNode(
        slug=slug,
        order_index=order_index,
        name=slug,
        required_level=required_level,
        gold_cost=gold_cost,
        monster_template_id=monster.id,
    )
    db_session.add(node)
    db_session.flush()
    return node


def _get_hero_id(client, token) -> uuid.UUID:
    me = client.get("/api/v1/users/me", headers=_auth(token)).json()
    return uuid.UUID(me["hero"]["id"])


def test_get_campaign_nodes_requires_auth(client):
    response = client.get("/api/v1/campaign/nodes")
    assert response.status_code in (401, 403)


def test_enter_campaign_node_requires_auth(client, db_session):
    node = _make_node(db_session, slug="camp-auth-1", order_index=1)
    response = client.post(f"/api/v1/campaign/nodes/{node.id}/enter")
    assert response.status_code in (401, 403)


def test_campaign_nodes_status_reflects_sequential_progress(client, db_session):
    token = _signup(client)
    node1 = _make_node(db_session, slug="camp-status-1", order_index=1)
    node2 = _make_node(db_session, slug="camp-status-2", order_index=2)

    response = client.get("/api/v1/campaign/nodes", headers=_auth(token))
    assert response.status_code == 200
    by_id = {n["id"]: n for n in response.json()}
    assert by_id[str(node1.id)]["status"] == "available"
    assert by_id[str(node2.id)]["status"] == "locked"


def test_entering_out_of_order_node_is_rejected(client, db_session):
    token = _signup(client, email="order@test.com")
    _make_node(db_session, slug="camp-order-1", order_index=1)
    node2 = _make_node(db_session, slug="camp-order-2", order_index=2)

    response = client.post(f"/api/v1/campaign/nodes/{node2.id}/enter", headers=_auth(token))
    assert response.status_code == 409


def test_entering_node_below_required_level_is_rejected(client, db_session):
    token = _signup(client, email="level@test.com")
    node = _make_node(db_session, slug="camp-level-1", order_index=1, required_level=5)

    response = client.post(f"/api/v1/campaign/nodes/{node.id}/enter", headers=_auth(token))
    assert response.status_code == 409


def test_entering_node_without_enough_gold_is_rejected(client, db_session):
    token = _signup(client, email="gold@test.com")
    node = _make_node(db_session, slug="camp-gold-1", order_index=1, gold_cost=100)

    response = client.post(f"/api/v1/campaign/nodes/{node.id}/enter", headers=_auth(token))
    assert response.status_code == 409


def test_entering_node_with_active_veil_run_is_rejected(client, db_session):
    token = _signup(client, email="active@test.com")
    node = _make_node(db_session, slug="camp-active-1", order_index=1)
    client.post("/api/v1/veil/enter", headers=_auth(token))

    response = client.post(f"/api/v1/campaign/nodes/{node.id}/enter", headers=_auth(token))
    assert response.status_code == 409


def test_entering_nonexistent_node_returns_404(client):
    token = _signup(client, email="missing@test.com")
    response = client.post(
        f"/api/v1/campaign/nodes/{uuid.uuid4()}/enter", headers=_auth(token)
    )
    assert response.status_code == 404


def test_entering_an_eligible_node_charges_gold_and_starts_a_hidden_run(client, db_session):
    token = _signup(client, email="enter@test.com")
    hero_id = _get_hero_id(client, token)
    hero = db_session.get(Hero, hero_id)
    hero.gold = 50
    db_session.flush()

    node = _make_node(db_session, slug="camp-enter-1", order_index=1, gold_cost=20)

    response = client.post(f"/api/v1/campaign/nodes/{node.id}/enter", headers=_auth(token))
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "in_progress"
    assert body["result"] is None

    me = client.get("/api/v1/users/me", headers=_auth(token)).json()
    assert me["hero"]["gold"] == 30


def test_claiming_a_campaign_run_advances_progress_and_clears_the_node(client, db_session):
    token = _signup(client, email="progress@test.com")
    hero_id = _get_hero_id(client, token)
    node = _make_node(db_session, slug="camp-progress-1", order_index=1)

    now = datetime.now(timezone.utc)
    run = VeilRun(
        hero_id=hero_id,
        campaign_node_id=node.id,
        seed=1,
        status=VeilRunStatus.IN_PROGRESS,
        started_at=now - timedelta(seconds=10),
        duration_seconds=5,
        resolves_at=now - timedelta(seconds=5),
        result_payload={
            "victory": True,
            "monster_name": "Test Monster",
            "log": [],
            "loot": [],
            "xp_awarded": 5,
        },
    )
    db_session.add(run)
    db_session.commit()

    claimed = client.post(f"/api/v1/veil/{run.id}/claim", headers=_auth(token)).json()
    assert claimed["status"] == "completed"

    hero = db_session.get(Hero, hero_id)
    db_session.refresh(hero)
    assert hero.campaign_progress == 1

    nodes = client.get("/api/v1/campaign/nodes", headers=_auth(token)).json()
    by_id = {n["id"]: n for n in nodes}
    assert by_id[str(node.id)]["status"] == "cleared"


def test_defeat_on_a_campaign_run_does_not_advance_progress(client, db_session):
    token = _signup(client, email="defeat@test.com")
    hero_id = _get_hero_id(client, token)
    node = _make_node(db_session, slug="camp-defeat-1", order_index=1)

    now = datetime.now(timezone.utc)
    run = VeilRun(
        hero_id=hero_id,
        campaign_node_id=node.id,
        seed=1,
        status=VeilRunStatus.IN_PROGRESS,
        started_at=now - timedelta(seconds=10),
        duration_seconds=5,
        resolves_at=now - timedelta(seconds=5),
        result_payload={
            "victory": False,
            "monster_name": "Test Monster",
            "log": [],
            "loot": [],
            "xp_awarded": 0,
        },
    )
    db_session.add(run)
    db_session.commit()

    claimed = client.post(f"/api/v1/veil/{run.id}/claim", headers=_auth(token)).json()
    assert claimed["status"] == "completed"

    hero = db_session.get(Hero, hero_id)
    db_session.refresh(hero)
    assert hero.campaign_progress == 0
