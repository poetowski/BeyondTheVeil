def _signup(client, email="leaderboard@test.com", hero_name="Ranker"):
    response = client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": "hunter22", "hero_name": hero_name},
    )
    return response.json()["access_token"]


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_leaderboard_requires_auth(client):
    response = client.get("/api/v1/leaderboard")
    assert response.status_code in (401, 403)


def test_leaderboard_is_just_the_signed_up_hero_when_alone(client):
    token = _signup(client, email="solo@test.com", hero_name="Solo")

    response = client.get("/api/v1/leaderboard", headers=_auth(token))

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0] == {"rank": 1, "name": "Solo", "level": 1}


def test_leaderboard_is_sorted_by_level_descending(client, db_session, hero_factory):
    token = _signup(client, email="viewer@test.com", hero_name="Viewer")
    hero_factory(name="Highest", level=10)
    hero_factory(name="Middle", level=5)
    hero_factory(name="Lowest", level=2)
    db_session.flush()

    response = client.get("/api/v1/leaderboard", headers=_auth(token))

    assert response.status_code == 200
    body = response.json()
    names_in_order = [entry["name"] for entry in body]
    # Viewer is level 1 (signup default) - lower than "Lowest" (level 2).
    assert names_in_order == ["Highest", "Middle", "Lowest", "Viewer"]
    assert [entry["rank"] for entry in body] == [1, 2, 3, 4]
    assert [entry["level"] for entry in body] == [10, 5, 2, 1]


def test_leaderboard_ties_are_broken_by_xp_descending(client, db_session, hero_factory):
    token = _signup(client, email="tiebreak@test.com", hero_name="TieViewer")
    hero_factory(name="TiedHighXp", level=5, xp=90)
    hero_factory(name="TiedLowXp", level=5, xp=10)
    db_session.flush()

    response = client.get("/api/v1/leaderboard", headers=_auth(token))

    assert response.status_code == 200
    names_in_order = [entry["name"] for entry in response.json() if entry["name"].startswith("Tied")]
    assert names_in_order == ["TiedHighXp", "TiedLowXp"]


def test_leaderboard_is_capped_at_10(client, db_session, hero_factory):
    token = _signup(client, email="crowded@test.com", hero_name="Crowded")
    for i in range(15):
        hero_factory(name=f"Filler{i}", level=i + 1)
    db_session.flush()

    response = client.get("/api/v1/leaderboard", headers=_auth(token))

    assert response.status_code == 200
    assert len(response.json()) == 10
