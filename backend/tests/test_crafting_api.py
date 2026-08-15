import uuid

from app.models.consumable import ConsumableInstance, ConsumableTemplate
from app.models.crafting import CraftingCategory, CraftingRecipe, CraftingRecipeIngredient
from app.models.hero import Hero
from app.models.item import EquipmentSlot, ItemInstance, ItemTemplate
from app.models.material import MaterialInstance, MaterialTemplate


def _signup(client, email="crafting@test.com", hero_name="Alchemist"):
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


def _make_recipe(
    db_session, *, slug, level_requirement=1, quantity_required=2, heal_flat=20, heal_vitality_multiplier=0
):
    material = MaterialTemplate(slug=f"{slug}-material", name=f"{slug} Material")
    consumable = ConsumableTemplate(
        slug=f"{slug}-elixir",
        name=f"{slug} Elixir",
        heal_flat=heal_flat,
        heal_vitality_multiplier=heal_vitality_multiplier,
    )
    db_session.add_all([material, consumable])
    db_session.flush()

    recipe = CraftingRecipe(
        slug=slug,
        name=slug,
        category=CraftingCategory.ALCHEMY,
        level_requirement=level_requirement,
        output_consumable_template_id=consumable.id,
        output_quantity=1,
    )
    db_session.add(recipe)
    db_session.flush()

    db_session.add(
        CraftingRecipeIngredient(
            recipe_id=recipe.id, material_template_id=material.id, quantity_required=quantity_required
        )
    )
    db_session.flush()
    return recipe, material, consumable


def test_get_recipes_requires_auth(client):
    response = client.get("/api/v1/crafting/recipes")
    assert response.status_code in (401, 403)


def test_recipe_shows_not_craftable_without_materials(client, db_session):
    token = _signup(client, email="norecipe@test.com")
    _make_recipe(db_session, slug="test-recipe-1", quantity_required=3)

    response = client.get("/api/v1/crafting/recipes", headers=_auth(token))
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["craftable"] is False
    assert body[0]["ingredients"][0]["quantity_owned"] == 0
    assert body[0]["ingredients"][0]["quantity_required"] == 3


def test_craft_without_enough_materials_is_rejected(client, db_session):
    token = _signup(client, email="shortmats@test.com")
    _make_recipe(db_session, slug="test-recipe-2", quantity_required=3)

    response = client.post("/api/v1/crafting/craft/test-recipe-2", headers=_auth(token))
    assert response.status_code == 409


def test_craft_unknown_recipe_returns_404(client):
    token = _signup(client, email="norecipe2@test.com")
    response = client.post("/api/v1/crafting/craft/does-not-exist", headers=_auth(token))
    assert response.status_code == 404


def test_craft_below_level_requirement_is_rejected(client, db_session):
    token = _signup(client, email="lowlevel@test.com")
    hero_id = _get_hero_id(client, token)
    recipe, material, _ = _make_recipe(db_session, slug="test-recipe-3", level_requirement=5, quantity_required=1)
    db_session.add(MaterialInstance(template_id=material.id, owner_hero_id=hero_id, quantity=5))
    db_session.flush()

    response = client.post("/api/v1/crafting/craft/test-recipe-3", headers=_auth(token))
    assert response.status_code == 409


def test_craft_deducts_materials_and_grants_consumable(client, db_session):
    token = _signup(client, email="craft@test.com")
    hero_id = _get_hero_id(client, token)
    recipe, material, consumable = _make_recipe(db_session, slug="test-recipe-4", quantity_required=3)
    db_session.add(MaterialInstance(template_id=material.id, owner_hero_id=hero_id, quantity=5))
    db_session.flush()

    response = client.post("/api/v1/crafting/craft/test-recipe-4", headers=_auth(token))
    assert response.status_code == 200
    body = response.json()
    assert body["output_type"] == "consumable"
    assert body["consumable"]["name"] == consumable.name
    assert body["consumable"]["quantity"] == 1
    assert body["rune"] is None

    materials = client.get("/api/v1/materials", headers=_auth(token)).json()
    assert len(materials) == 1
    assert materials[0]["quantity"] == 2, "5 owned - 3 required == 2 remaining"

    consumables = client.get("/api/v1/consumables", headers=_auth(token)).json()
    assert len(consumables) == 1
    assert consumables[0]["quantity"] == 1
    assert consumables[0]["slug"] == consumable.slug


def test_craft_rejected_when_backpack_is_full(client, db_session):
    token = _signup(client, email="fullbackpack@test.com")
    hero_id = _get_hero_id(client, token)
    hero = db_session.get(Hero, hero_id)
    hero.inventory_capacity = 1
    db_session.flush()

    recipe, material, _ = _make_recipe(db_session, slug="test-recipe-9", quantity_required=1)
    db_session.add(MaterialInstance(template_id=material.id, owner_hero_id=hero_id, quantity=5))
    db_session.flush()

    # Fill the single backpack slot with an unrelated item first.
    blocker_template = ItemTemplate(
        slug="test-recipe-9-blocker", name="Blocker", slot=EquipmentSlot.HELMET, base_stats={}
    )
    db_session.add(blocker_template)
    db_session.flush()
    db_session.add(
        ItemInstance(template_id=blocker_template.id, owner_hero_id=hero_id, equipped_slot=None)
    )
    db_session.flush()

    response = client.post("/api/v1/crafting/craft/test-recipe-9", headers=_auth(token))
    assert response.status_code == 409

    materials = client.get("/api/v1/materials", headers=_auth(token)).json()
    assert materials[0]["quantity"] == 5, "materials must not be deducted when craft is rejected for space"
    assert client.get("/api/v1/consumables", headers=_auth(token)).json() == []


def test_craft_rejected_when_existing_consumables_fill_the_backpack(client, db_session):
    token = _signup(client, email="fullofpotions@test.com")
    hero_id = _get_hero_id(client, token)
    hero = db_session.get(Hero, hero_id)
    hero.inventory_capacity = 2
    db_session.flush()

    recipe, material, consumable_template = _make_recipe(
        db_session, slug="test-recipe-10", quantity_required=1
    )
    db_session.add(MaterialInstance(template_id=material.id, owner_hero_id=hero_id, quantity=5))
    # Already carrying 2 of this potion - exactly at the (quantity-based) cap.
    db_session.add(
        ConsumableInstance(template_id=consumable_template.id, owner_hero_id=hero_id, quantity=2)
    )
    db_session.flush()

    response = client.post("/api/v1/crafting/craft/test-recipe-10", headers=_auth(token))
    assert response.status_code == 409

    materials = client.get("/api/v1/materials", headers=_auth(token)).json()
    assert materials[0]["quantity"] == 5, "materials must not be deducted when craft is rejected for space"


def test_craft_twice_stacks_the_consumable(client, db_session):
    token = _signup(client, email="craftstack@test.com")
    hero_id = _get_hero_id(client, token)
    recipe, material, _ = _make_recipe(db_session, slug="test-recipe-5", quantity_required=1)
    db_session.add(MaterialInstance(template_id=material.id, owner_hero_id=hero_id, quantity=10))
    db_session.flush()

    client.post("/api/v1/crafting/craft/test-recipe-5", headers=_auth(token))
    client.post("/api/v1/crafting/craft/test-recipe-5", headers=_auth(token))

    consumables = client.get("/api/v1/consumables", headers=_auth(token)).json()
    assert len(consumables) == 1
    assert consumables[0]["quantity"] == 2


def test_use_consumable_heals_hp_and_depletes_the_stack(client, db_session):
    token = _signup(client, email="useit@test.com")
    hero_id = _get_hero_id(client, token)
    hero = db_session.get(Hero, hero_id)
    hero.current_hp = 10
    db_session.flush()

    _, _, consumable_template = _make_recipe(
        db_session, slug="test-recipe-6", heal_flat=20, heal_vitality_multiplier=2
    )
    instance = ConsumableInstance(
        template_id=consumable_template.id, owner_hero_id=hero_id, quantity=1
    )
    db_session.add(instance)
    db_session.flush()

    response = client.post(f"/api/v1/consumables/{instance.id}/use", headers=_auth(token))
    assert response.status_code == 200
    body = response.json()
    expected_heal = round(20 + 2 * body["vitality"])
    assert body["current_hp"] == min(body["max_hp"], 10 + expected_heal)

    consumables = client.get("/api/v1/consumables", headers=_auth(token)).json()
    assert consumables == []


def test_use_consumable_never_exceeds_max_hp(client, db_session):
    token = _signup(client, email="capuse@test.com")
    hero_id = _get_hero_id(client, token)

    _, _, consumable_template = _make_recipe(
        db_session, slug="test-recipe-7", heal_flat=100_000, heal_vitality_multiplier=0
    )
    instance = ConsumableInstance(
        template_id=consumable_template.id, owner_hero_id=hero_id, quantity=1
    )
    db_session.add(instance)
    db_session.flush()

    response = client.post(f"/api/v1/consumables/{instance.id}/use", headers=_auth(token))
    body = response.json()
    assert body["current_hp"] == body["max_hp"]


def test_use_of_unowned_consumable_is_rejected(client, db_session):
    owner_token = _signup(client, email="owner-c@test.com", hero_name="Owner")
    owner_id = _get_hero_id(client, owner_token)
    _, _, consumable_template = _make_recipe(db_session, slug="test-recipe-8")
    instance = ConsumableInstance(
        template_id=consumable_template.id, owner_hero_id=owner_id, quantity=1
    )
    db_session.add(instance)
    db_session.flush()

    intruder_token = _signup(client, email="intruder-c@test.com", hero_name="Intruder")
    response = client.post(
        f"/api/v1/consumables/{instance.id}/use", headers=_auth(intruder_token)
    )
    assert response.status_code == 403


def test_use_of_nonexistent_consumable_returns_404(client):
    token = _signup(client, email="ghost-c@test.com")
    response = client.post(
        f"/api/v1/consumables/{uuid.uuid4()}/use", headers=_auth(token)
    )
    assert response.status_code == 404
