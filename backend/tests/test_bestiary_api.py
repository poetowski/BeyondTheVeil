from app.models.monster import MonsterTemplate


def _signup(client, email="bestiary@test.com", hero_name="Quennel"):
    response = client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": "hunter22", "hero_name": hero_name},
    )
    return response.json()["access_token"]


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_bestiary_requires_auth(client):
    response = client.get("/api/v1/bestiary")
    assert response.status_code in (401, 403)


def test_bestiary_lists_monster_templates(client, db_session):
    token = _signup(client)

    monster = MonsterTemplate(
        slug="test-bestiary-wisp",
        name="Test Bestiary Wisp",
        level_range_min=1,
        level_range_max=2,
        base_stats={"strength": 1, "dexterity": 1, "vitality": 1, "agility": 1, "intelligence": 1, "spirit": 1},
        flavor_text="A flicker of something that shouldn't exist.",
    )
    db_session.add(monster)
    db_session.flush()

    response = client.get("/api/v1/bestiary", headers=_auth(token))

    assert response.status_code == 200
    by_slug = {entry["slug"]: entry for entry in response.json()}
    assert "test-bestiary-wisp" in by_slug
    assert by_slug["test-bestiary-wisp"]["name"] == "Test Bestiary Wisp"
    assert by_slug["test-bestiary-wisp"]["level_range_min"] == 1
    assert by_slug["test-bestiary-wisp"]["level_range_max"] == 2
    assert by_slug["test-bestiary-wisp"]["flavor_text"] == "A flicker of something that shouldn't exist."
