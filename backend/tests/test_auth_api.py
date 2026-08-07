from sqlalchemy import select

from app.models.hero import Hero
from app.models.user import User
from app.services.hero_service import BASELINE_STAT_VALUE, STAT_NAMES


def test_signup_creates_user_and_hero_and_returns_token(client, db_session):
    response = client.post(
        "/api/v1/auth/signup",
        json={"email": "signup@test.com", "password": "hunter22", "hero_name": "Ashe"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]

    user = db_session.execute(select(User).where(User.email == "signup@test.com")).scalar_one()
    hero = db_session.execute(select(Hero).where(Hero.user_id == user.id)).scalar_one()
    assert hero.name == "Ashe"
    for stat in STAT_NAMES:
        assert getattr(hero, stat) == BASELINE_STAT_VALUE


def test_signup_duplicate_email_is_rejected(client, db_session):
    payload = {"email": "dupe@test.com", "password": "hunter22", "hero_name": "First"}
    first = client.post("/api/v1/auth/signup", json=payload)
    assert first.status_code == 200

    second = client.post(
        "/api/v1/auth/signup",
        json={**payload, "hero_name": "Second"},
    )
    assert second.status_code == 409

    users = db_session.execute(select(User).where(User.email == "dupe@test.com")).scalars().all()
    assert len(users) == 1


def test_login_with_correct_credentials_returns_usable_token(client):
    client.post(
        "/api/v1/auth/signup",
        json={"email": "login@test.com", "password": "hunter22", "hero_name": "Bram"},
    )

    login_response = client.post(
        "/api/v1/auth/login", json={"email": "login@test.com", "password": "hunter22"}
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    me_response = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
    assert me_response.status_code == 200
    assert me_response.json()["hero"]["name"] == "Bram"


def test_login_rejects_wrong_password(client):
    client.post(
        "/api/v1/auth/signup",
        json={"email": "wrongpw@test.com", "password": "hunter22", "hero_name": "Cato"},
    )

    response = client.post(
        "/api/v1/auth/login", json={"email": "wrongpw@test.com", "password": "not-the-password"}
    )
    assert response.status_code == 401


def test_login_rejects_unknown_email(client):
    response = client.post(
        "/api/v1/auth/login", json={"email": "nobody@test.com", "password": "irrelevant"}
    )
    assert response.status_code == 401


def test_login_error_message_does_not_leak_which_field_was_wrong(client):
    client.post(
        "/api/v1/auth/signup",
        json={"email": "leaktest@test.com", "password": "hunter22", "hero_name": "Dax"},
    )

    unknown_email = client.post(
        "/api/v1/auth/login", json={"email": "unknown@test.com", "password": "hunter22"}
    )
    wrong_password = client.post(
        "/api/v1/auth/login", json={"email": "leaktest@test.com", "password": "wrong"}
    )

    assert unknown_email.json()["detail"] == wrong_password.json()["detail"]
