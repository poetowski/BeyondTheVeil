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


def test_new_hero_defaults_to_peasant_avatar(client):
    token = _signup(client, email="hero-api-avatar-default@test.com")
    me = client.get("/api/v1/users/me", headers=_auth(token)).json()
    assert me["hero"]["avatar_slug"] == "peasant-avatar"


def test_get_avatars_lists_all_avatar_templates(client):
    token = _signup(client, email="hero-api-avatars-list@test.com")
    response = client.get("/api/v1/avatars", headers=_auth(token))
    assert response.status_code == 200
    slugs = {avatar["slug"] for avatar in response.json()}
    assert slugs == {"peasant-avatar"}


def test_set_avatar_updates_the_hero(client, db_session):
    from app.models.avatar import AvatarTemplate

    db_session.add(AvatarTemplate(slug="militia-avatar", name="Militia Avatar"))
    db_session.flush()

    token = _signup(client, email="hero-api-set-avatar@test.com")
    response = client.post(
        "/api/v1/hero/avatar", json={"avatar_slug": "militia-avatar"}, headers=_auth(token)
    )

    assert response.status_code == 200
    assert response.json()["avatar_slug"] == "militia-avatar"


def test_set_avatar_with_unknown_slug_is_rejected(client):
    token = _signup(client, email="hero-api-set-avatar-bad@test.com")
    response = client.post(
        "/api/v1/hero/avatar", json={"avatar_slug": "nonexistent-avatar"}, headers=_auth(token)
    )
    assert response.status_code == 404


def test_get_avatars_orders_peasant_before_militia(client, db_session):
    from app.models.avatar import AvatarTemplate

    db_session.add(AvatarTemplate(slug="militia-avatar", name="Militia Avatar", price=2000, sort_order=1))
    db_session.flush()

    token = _signup(client, email="hero-api-avatars-order@test.com")
    response = client.get("/api/v1/avatars", headers=_auth(token))
    slugs = [avatar["slug"] for avatar in response.json()]
    assert slugs == ["peasant-avatar", "militia-avatar"]


def test_set_avatar_on_a_locked_paid_avatar_is_rejected(client, db_session):
    from app.models.avatar import AvatarTemplate

    db_session.add(AvatarTemplate(slug="militia-avatar", name="Militia Avatar", price=2000, sort_order=1))
    db_session.flush()

    token = _signup(client, email="hero-api-set-avatar-locked@test.com")
    response = client.post(
        "/api/v1/hero/avatar", json={"avatar_slug": "militia-avatar"}, headers=_auth(token)
    )
    assert response.status_code == 403


def test_unlock_avatar_charges_gold_and_unlocks_it(client, db_session):
    from app.models.avatar import AvatarTemplate
    from app.models.hero import Hero

    db_session.add(AvatarTemplate(slug="militia-avatar", name="Militia Avatar", price=2000, sort_order=1))
    db_session.flush()

    token = _signup(client, email="hero-api-unlock-avatar@test.com")
    me = client.get("/api/v1/users/me", headers=_auth(token)).json()
    hero = db_session.get(Hero, me["hero"]["id"])
    hero.gold = 5000
    db_session.flush()

    unlock_response = client.post("/api/v1/avatars/militia-avatar/unlock", headers=_auth(token))
    assert unlock_response.status_code == 200
    assert unlock_response.json()["gold"] == 3000

    avatars = client.get("/api/v1/avatars", headers=_auth(token)).json()
    militia = next(a for a in avatars if a["slug"] == "militia-avatar")
    assert militia["unlocked"] is True

    select_response = client.post(
        "/api/v1/hero/avatar", json={"avatar_slug": "militia-avatar"}, headers=_auth(token)
    )
    assert select_response.status_code == 200
    assert select_response.json()["avatar_slug"] == "militia-avatar"


def test_unlock_avatar_without_enough_gold_is_rejected(client, db_session):
    from app.models.avatar import AvatarTemplate

    db_session.add(AvatarTemplate(slug="militia-avatar", name="Militia Avatar", price=2000, sort_order=1))
    db_session.flush()

    token = _signup(client, email="hero-api-unlock-avatar-poor@test.com")
    response = client.post("/api/v1/avatars/militia-avatar/unlock", headers=_auth(token))
    assert response.status_code == 409


def test_unlock_avatar_with_unknown_slug_returns_404(client):
    token = _signup(client, email="hero-api-unlock-avatar-bad@test.com")
    response = client.post("/api/v1/avatars/nonexistent-avatar/unlock", headers=_auth(token))
    assert response.status_code == 404


def test_level_gated_avatar_is_locked_below_its_level_requirement(client, db_session):
    from app.models.avatar import AvatarTemplate

    db_session.add(
        AvatarTemplate(slug="warrior-avatar", name="Warrior Avatar", level_requirement=10, sort_order=2)
    )
    db_session.flush()

    token = _signup(client, email="hero-api-warrior-locked@test.com")
    avatars = client.get("/api/v1/avatars", headers=_auth(token)).json()
    warrior = next(a for a in avatars if a["slug"] == "warrior-avatar")
    assert warrior["unlocked"] is False
    assert warrior["level_requirement"] == 10

    select_response = client.post(
        "/api/v1/hero/avatar", json={"avatar_slug": "warrior-avatar"}, headers=_auth(token)
    )
    assert select_response.status_code == 403


def test_unlock_endpoint_rejects_a_free_avatar_not_yet_level_eligible(client, db_session):
    from app.models.avatar import AvatarTemplate

    db_session.add(
        AvatarTemplate(slug="warrior-avatar", name="Warrior Avatar", level_requirement=10, sort_order=2)
    )
    db_session.flush()

    token = _signup(client, email="hero-api-warrior-unlock-too-early@test.com")
    response = client.post("/api/v1/avatars/warrior-avatar/unlock", headers=_auth(token))
    assert response.status_code == 403


def test_avatar_auto_unlocks_once_hero_reaches_its_level_requirement(client, db_session):
    from app.models.avatar import AvatarTemplate
    from app.models.hero import Hero

    db_session.add(
        AvatarTemplate(slug="warrior-avatar", name="Warrior Avatar", level_requirement=10, sort_order=2)
    )
    db_session.flush()

    token = _signup(client, email="hero-api-warrior-auto-unlock@test.com")
    me = client.get("/api/v1/users/me", headers=_auth(token)).json()
    hero = db_session.get(Hero, me["hero"]["id"])
    hero.level = 10
    db_session.flush()

    avatars = client.get("/api/v1/avatars", headers=_auth(token)).json()
    warrior = next(a for a in avatars if a["slug"] == "warrior-avatar")
    assert warrior["unlocked"] is True

    select_response = client.post(
        "/api/v1/hero/avatar", json={"avatar_slug": "warrior-avatar"}, headers=_auth(token)
    )
    assert select_response.status_code == 200
    assert select_response.json()["avatar_slug"] == "warrior-avatar"


def test_unlock_hint_avatar_stays_locked_even_past_its_level_requirement(client, db_session):
    # price=0 alone isn't enough once unlock_hint is set - see
    # AvatarTemplate's docstring and hero_service.is_avatar_unlocked. Unlike
    # Warrior Avatar above, reaching the level must NOT be sufficient here.
    from app.models.avatar import AvatarTemplate
    from app.models.hero import Hero

    db_session.add(
        AvatarTemplate(
            slug="flower-kid-avatar",
            name="Flower Kid Avatar",
            level_requirement=15,
            sort_order=5,
            unlock_hint="Craft a Herbalist Hell potion in Alchemy (level 15) and drink it.",
        )
    )
    db_session.flush()

    token = _signup(client, email="hero-api-flower-kid-locked@test.com")
    me = client.get("/api/v1/users/me", headers=_auth(token)).json()
    hero = db_session.get(Hero, me["hero"]["id"])
    hero.level = 15
    db_session.flush()

    avatars = client.get("/api/v1/avatars", headers=_auth(token)).json()
    flower_kid = next(a for a in avatars if a["slug"] == "flower-kid-avatar")
    assert flower_kid["unlocked"] is False
    assert flower_kid["unlock_hint"] == "Craft a Herbalist Hell potion in Alchemy (level 15) and drink it."

    select_response = client.post(
        "/api/v1/hero/avatar", json={"avatar_slug": "flower-kid-avatar"}, headers=_auth(token)
    )
    assert select_response.status_code == 403

    unlock_response = client.post("/api/v1/avatars/flower-kid-avatar/unlock", headers=_auth(token))
    assert unlock_response.status_code == 403, "price=0 avatars are never purchasable, unlock_hint or not"


def test_unlock_hint_is_null_for_ordinary_avatars(client, db_session):
    from app.models.avatar import AvatarTemplate

    db_session.add(AvatarTemplate(slug="militia-avatar", name="Militia Avatar", price=2000, sort_order=1))
    db_session.flush()

    token = _signup(client, email="hero-api-unlock-hint-null@test.com")
    avatars = client.get("/api/v1/avatars", headers=_auth(token)).json()
    militia = next(a for a in avatars if a["slug"] == "militia-avatar")
    assert militia["unlock_hint"] is None


def test_grant_avatar_unlock_is_idempotent(db_session, hero_factory):
    from app.models.avatar import AvatarTemplate, HeroAvatarUnlock

    hero = hero_factory()
    avatar = AvatarTemplate(
        slug="flower-kid-avatar", name="Flower Kid Avatar", level_requirement=15, sort_order=5,
        unlock_hint="Craft a Herbalist Hell potion in Alchemy (level 15) and drink it.",
    )
    db_session.add(avatar)
    db_session.flush()

    hero_service.grant_avatar_unlock(db_session, hero, "flower-kid-avatar")
    hero_service.grant_avatar_unlock(db_session, hero, "flower-kid-avatar")
    db_session.flush()

    unlocks = db_session.query(HeroAvatarUnlock).filter_by(hero_id=hero.id).all()
    assert len(unlocks) == 1


def test_grant_avatar_unlock_on_unknown_slug_is_a_silent_no_op(db_session, hero_factory):
    hero = hero_factory()
    hero_service.grant_avatar_unlock(db_session, hero, "nonexistent-avatar")
    db_session.flush()
