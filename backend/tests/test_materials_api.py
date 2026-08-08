from app.models.material import MaterialInstance, MaterialTemplate


def _signup(client, email="materials@test.com", hero_name="Fenwick"):
    response = client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": "hunter22", "hero_name": hero_name},
    )
    return response.json()["access_token"]


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_materials_requires_auth(client):
    response = client.get("/api/v1/materials")
    assert response.status_code in (401, 403)


def test_materials_is_empty_for_a_fresh_hero(client):
    token = _signup(client)

    response = client.get("/api/v1/materials", headers=_auth(token))

    assert response.status_code == 200
    assert response.json() == []


def test_materials_lists_owned_stacks_with_quantity(client, db_session):
    token = _signup(client, email="stocked-materials@test.com")

    me = client.get("/api/v1/users/me", headers=_auth(token)).json()
    hero_id = me["hero"]["id"]

    template = MaterialTemplate(
        slug="veil-dust", name="Veil Dust", description="A fine, shimmering residue."
    )
    db_session.add(template)
    db_session.flush()

    db_session.add(
        MaterialInstance(template_id=template.id, owner_hero_id=hero_id, quantity=3)
    )
    db_session.flush()

    response = client.get("/api/v1/materials", headers=_auth(token))

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["name"] == "Veil Dust"
    assert body[0]["quantity"] == 3
