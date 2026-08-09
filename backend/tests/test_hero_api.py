from app.services import hero_service


def _signup(client, email="hero-api@test.com", hero_name="Wren"):
    response = client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": "hunter22", "hero_name": hero_name},
    )
    return response.json()["access_token"]


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_train_stat_requires_auth(client):
    response = client.post("/api/v1/hero/train", json={"stat": "strength"})
    assert response.status_code in (401, 403)


def test_train_stat_rejects_an_unknown_stat_via_request_validation(client):
    token = _signup(client)
    response = client.post("/api/v1/hero/train", json={"stat": "luck"}, headers=_auth(token))
    assert response.status_code == 422


def test_train_stat_without_enough_gold_is_rejected(client):
    token = _signup(client, email="hero-api-poor@test.com")
    response = client.post("/api/v1/hero/train", json={"stat": "strength"}, headers=_auth(token))
    assert response.status_code == 409


def test_train_stat_spends_gold_and_returns_the_updated_hero(client, db_session):
    from app.models.hero import Hero

    token = _signup(client, email="hero-api-rich@test.com")
    me = client.get("/api/v1/users/me", headers=_auth(token)).json()
    hero = db_session.get(Hero, me["hero"]["id"])
    hero.gold = 100
    db_session.flush()

    response = client.post("/api/v1/hero/train", json={"stat": "strength"}, headers=_auth(token))

    assert response.status_code == 200
    body = response.json()
    assert body["strength"] == 11
    assert body["base_strength"] == 11
    assert body["gold"] == 100 - hero_service.TRAIN_STAT_BASE_COST
    # Training strength again should now cost more (power curve, not flat).
    assert body["train_costs"]["strength"] == hero_service.train_stat_cost(11)
    assert body["train_costs"]["strength"] > hero_service.TRAIN_STAT_BASE_COST
