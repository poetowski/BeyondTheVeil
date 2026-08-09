from app.services.hero_service import BASE_HP, BASELINE_STAT_VALUE, HP_PER_VITALITY, STAT_NAMES


def _signup(client, email="me@test.com", hero_name="Elowen"):
    response = client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": "hunter22", "hero_name": hero_name},
    )
    return response.json()["access_token"]


def test_get_me_requires_auth(client):
    response = client.get("/api/v1/users/me")
    assert response.status_code in (401, 403)  # missing Authorization header


def test_get_me_rejects_invalid_token(client):
    response = client.get(
        "/api/v1/users/me", headers={"Authorization": "Bearer not-a-real-token"}
    )
    assert response.status_code == 401


def test_get_me_returns_hero_and_user(client):
    token = _signup(client)

    response = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    body = response.json()
    assert body["user"]["email"] == "me@test.com"
    assert body["hero"]["name"] == "Elowen"
    assert body["hero"]["level"] == 1
    assert body["hero"]["xp"] == 0
    assert body["hero"]["inventory_capacity"] == 20
    expected_max_hp = BASE_HP + BASELINE_STAT_VALUE * HP_PER_VITALITY
    assert body["hero"]["max_hp"] == expected_max_hp

    for stat in STAT_NAMES:
        assert body["hero"][stat] == BASELINE_STAT_VALUE
        assert body["hero"][f"base_{stat}"] == BASELINE_STAT_VALUE
        assert body["hero"][f"bonus_{stat}"] == 0
