import uuid
from datetime import datetime, timedelta, timezone

from app.models.hero import Hero
from app.models.veil_run import VeilRun, VeilRunStatus


def _signup(client, email="leveling@test.com", hero_name="Wren"):
    response = client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": "hunter22", "hero_name": hero_name},
    )
    return response.json()["access_token"]


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _get_hero_id(client, token) -> uuid.UUID:
    me = client.get("/api/v1/users/me", headers=_auth(token)).json()
    return uuid.UUID(me["hero"]["id"])


def _claim_with_xp(client, db_session, token, hero_id, xp_awarded, *, victory=True) -> dict:
    now = datetime.now(timezone.utc)
    run = VeilRun(
        hero_id=hero_id,
        seed=1,
        status=VeilRunStatus.IN_PROGRESS,
        started_at=now - timedelta(seconds=10),
        duration_seconds=5,
        resolves_at=now - timedelta(seconds=5),
        result_payload={
            "victory": victory,
            "monster_name": "Test Monster",
            "log": [],
            "loot": [],
            "xp_awarded": xp_awarded,
        },
    )
    db_session.add(run)
    db_session.commit()
    return client.post(f"/api/v1/veil/{run.id}/claim", headers=_auth(token)).json()


def test_fresh_hero_starts_at_level_1_with_no_stat_points(client):
    token = _signup(client, email="fresh@test.com")
    me = client.get("/api/v1/users/me", headers=_auth(token)).json()
    hero = me["hero"]

    assert hero["level"] == 1
    assert hero["available_stat_points"] == 0
    assert hero["xp_into_level"] == 0
    assert hero["xp_for_next_level"] == 100


def test_claiming_enough_xp_levels_up_and_grants_stat_points(client, db_session):
    token = _signup(client, email="levelup@test.com")
    hero_id = _get_hero_id(client, token)

    claimed = _claim_with_xp(client, db_session, token, hero_id, xp_awarded=100)
    assert claimed["status"] == "completed"

    me = client.get("/api/v1/users/me", headers=_auth(token)).json()["hero"]
    assert me["level"] == 2
    assert me["available_stat_points"] == 3
    assert me["xp"] == 100
    assert me["xp_into_level"] == 0
    assert me["xp_for_next_level"] == 200


def test_large_xp_reward_crosses_multiple_levels_at_once(client, db_session):
    token = _signup(client, email="bigxp@test.com")
    hero_id = _get_hero_id(client, token)

    # xp_required_for_level(3) == 100*2*3/2 == 300, so this jumps level 1 -> 3.
    claimed = _claim_with_xp(client, db_session, token, hero_id, xp_awarded=300)
    assert claimed["status"] == "completed"

    me = client.get("/api/v1/users/me", headers=_auth(token)).json()["hero"]
    assert me["level"] == 3
    assert me["available_stat_points"] == 6
    assert me["xp_into_level"] == 0
    assert me["xp_for_next_level"] == 300


def test_defeat_awards_no_xp_and_no_level_up(client, db_session):
    token = _signup(client, email="defeat-lvl@test.com")
    hero_id = _get_hero_id(client, token)

    claimed = _claim_with_xp(client, db_session, token, hero_id, xp_awarded=0, victory=False)
    assert claimed["status"] == "completed"

    me = client.get("/api/v1/users/me", headers=_auth(token)).json()["hero"]
    assert me["level"] == 1
    assert me["available_stat_points"] == 0


def test_allocate_stat_requires_auth(client):
    response = client.post(
        "/api/v1/hero/allocate-stat", json={"stat": "strength", "amount": 1}
    )
    assert response.status_code in (401, 403)


def test_allocate_stat_spends_points_and_raises_the_stat(client, db_session):
    token = _signup(client, email="allocate@test.com")
    hero_id = _get_hero_id(client, token)
    hero = db_session.get(Hero, hero_id)
    hero.available_stat_points = 5
    db_session.flush()
    starting_strength = hero.strength

    response = client.post(
        "/api/v1/hero/allocate-stat",
        json={"stat": "strength", "amount": 3},
        headers=_auth(token),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["strength"] == starting_strength + 3
    assert body["base_strength"] == starting_strength + 3
    assert body["available_stat_points"] == 2


def test_allocate_stat_rejects_unknown_stat(client, db_session):
    token = _signup(client, email="badstat@test.com")
    hero_id = _get_hero_id(client, token)
    hero = db_session.get(Hero, hero_id)
    hero.available_stat_points = 5
    db_session.flush()

    response = client.post(
        "/api/v1/hero/allocate-stat",
        json={"stat": "luck", "amount": 1},
        headers=_auth(token),
    )
    assert response.status_code == 422


def test_allocate_stat_rejects_non_positive_amount(client, db_session):
    token = _signup(client, email="zeroamount@test.com")
    hero_id = _get_hero_id(client, token)
    hero = db_session.get(Hero, hero_id)
    hero.available_stat_points = 5
    db_session.flush()

    response = client.post(
        "/api/v1/hero/allocate-stat",
        json={"stat": "strength", "amount": 0},
        headers=_auth(token),
    )
    assert response.status_code == 400


def test_allocate_stat_rejects_spending_more_points_than_available(client, db_session):
    token = _signup(client, email="overspend@test.com")
    hero_id = _get_hero_id(client, token)
    hero = db_session.get(Hero, hero_id)
    hero.available_stat_points = 1
    db_session.flush()

    response = client.post(
        "/api/v1/hero/allocate-stat",
        json={"stat": "strength", "amount": 2},
        headers=_auth(token),
    )
    assert response.status_code == 409
