import uuid

from app.models.crafting import CraftingCategory, CraftingRecipe, CraftingRecipeIngredient
from app.models.hero import Hero
from app.models.item import EquipmentSlot, ItemInstance, ItemTemplate
from app.models.material import MaterialInstance, MaterialTemplate
from app.models.rune import RuneInstance, RuneTemplate
from app.services import hero_service


def _signup(client, email="runes@test.com", hero_name="Smith"):
    response = client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": "hunter22", "hero_name": hero_name},
    )
    return response.json()["access_token"]


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _hero_id(client, token) -> uuid.UUID:
    me = client.get("/api/v1/users/me", headers=_auth(token)).json()
    return uuid.UUID(me["hero"]["id"])


def _make_rune_recipe(db_session, *, slug, level_requirement=1, quantity_required=2, stat_bonuses=None):
    material = MaterialTemplate(
        slug=f"{slug}-ore", name=f"{slug} Ore", category=CraftingCategory.FORGE
    )
    rune = RuneTemplate(
        slug=f"{slug}-rune", name=f"{slug} Rune", stat_bonuses=stat_bonuses or {"strength": 3}
    )
    db_session.add_all([material, rune])
    db_session.flush()

    recipe = CraftingRecipe(
        slug=slug,
        name=slug,
        category=CraftingCategory.FORGE,
        level_requirement=level_requirement,
        output_rune_template_id=rune.id,
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
    return recipe, material, rune


# --- compute_stat_bonuses: rune contribution ---------------------------------


def test_rune_bonus_applies_only_while_host_item_is_equipped():
    hero = Hero(strength=5, dexterity=5, vitality=5, agility=5, intelligence=5, spirit=5)
    rune_template = RuneTemplate(slug="vigor", name="Rune of Vigor", stat_bonuses={"vitality": 3})
    item_template = ItemTemplate(
        slug="ringed-blade", name="Ringed Blade", slot=EquipmentSlot.WEAPON, base_stats={}
    )

    equipped = ItemInstance(equipped_slot=EquipmentSlot.WEAPON)
    equipped.template = item_template
    equipped.rune_template = rune_template

    unequipped = ItemInstance(equipped_slot=None)
    unequipped.template = item_template
    unequipped.rune_template = rune_template

    bonuses_equipped = hero_service.compute_stat_bonuses(hero, [equipped])
    bonuses_unequipped = hero_service.compute_stat_bonuses(hero, [unequipped])

    assert bonuses_equipped["vitality"] == 3
    assert bonuses_unequipped["vitality"] == 0


def test_item_without_a_rune_contributes_no_rune_bonus():
    hero = Hero(strength=5, dexterity=5, vitality=5, agility=5, intelligence=5, spirit=5)
    item_template = ItemTemplate(
        slug="plain-blade", name="Plain Blade", slot=EquipmentSlot.WEAPON, base_stats={}
    )
    item = ItemInstance(equipped_slot=EquipmentSlot.WEAPON)
    item.template = item_template

    bonuses = hero_service.compute_stat_bonuses(hero, [item])
    assert all(v == 0 for v in bonuses.values())


# --- apply_rune (service + API) ----------------------------------------------


def test_apply_rune_sets_item_rune_and_consumes_the_stack(db_session, hero_factory):
    hero = hero_factory()
    rune_template = RuneTemplate(slug="might", name="Rune of Might", stat_bonuses={"strength": 3})
    item_template = ItemTemplate(
        slug="test-apply-sword", name="Test Sword", slot=EquipmentSlot.WEAPON, base_stats={}
    )
    db_session.add_all([rune_template, item_template])
    db_session.flush()

    item = ItemInstance(template_id=item_template.id, owner_hero_id=hero.id, equipped_slot=None)
    rune_instance = RuneInstance(template_id=rune_template.id, owner_hero_id=hero.id, quantity=1)
    db_session.add_all([item, rune_instance])
    db_session.flush()

    updated = hero_service.apply_rune(db_session, hero, item.id, rune_instance.id)

    assert updated.rune_template_id == rune_template.id
    assert db_session.get(RuneInstance, rune_instance.id) is None, "single-unit stack should be deleted"


def test_apply_rune_decrements_a_multi_unit_stack(db_session, hero_factory):
    hero = hero_factory()
    rune_template = RuneTemplate(slug="might2", name="Rune of Might II", stat_bonuses={"strength": 3})
    item_template = ItemTemplate(
        slug="test-apply-sword-2", name="Test Sword 2", slot=EquipmentSlot.WEAPON, base_stats={}
    )
    db_session.add_all([rune_template, item_template])
    db_session.flush()

    item = ItemInstance(template_id=item_template.id, owner_hero_id=hero.id, equipped_slot=None)
    rune_instance = RuneInstance(template_id=rune_template.id, owner_hero_id=hero.id, quantity=3)
    db_session.add_all([item, rune_instance])
    db_session.flush()

    hero_service.apply_rune(db_session, hero, item.id, rune_instance.id)

    remaining = db_session.get(RuneInstance, rune_instance.id)
    assert remaining is not None
    assert remaining.quantity == 2


def test_apply_rune_rejects_an_item_that_already_has_one(db_session, hero_factory):
    hero = hero_factory()
    first_rune = RuneTemplate(slug="first", name="First Rune", stat_bonuses={"strength": 1})
    second_rune = RuneTemplate(slug="second", name="Second Rune", stat_bonuses={"strength": 1})
    item_template = ItemTemplate(
        slug="test-double-rune-sword", name="Test Sword 3", slot=EquipmentSlot.WEAPON, base_stats={}
    )
    db_session.add_all([first_rune, second_rune, item_template])
    db_session.flush()

    item = ItemInstance(
        template_id=item_template.id,
        owner_hero_id=hero.id,
        equipped_slot=None,
        rune_template_id=first_rune.id,
    )
    second_instance = RuneInstance(template_id=second_rune.id, owner_hero_id=hero.id, quantity=1)
    db_session.add_all([item, second_instance])
    db_session.flush()

    try:
        hero_service.apply_rune(db_session, hero, item.id, second_instance.id)
        assert False, "expected RuneAlreadyAppliedError"
    except hero_service.RuneAlreadyAppliedError:
        pass


def test_apply_rune_api_rejects_unowned_item_or_rune(client, db_session):
    owner_token = _signup(client, email="rune-owner@test.com", hero_name="Owner")
    owner_id = _hero_id(client, owner_token)
    intruder_token = _signup(client, email="rune-intruder@test.com", hero_name="Intruder")

    rune_template = RuneTemplate(slug="api-rune", name="API Rune", stat_bonuses={"strength": 1})
    item_template = ItemTemplate(
        slug="test-api-rune-sword", name="Test Sword 4", slot=EquipmentSlot.WEAPON, base_stats={}
    )
    db_session.add_all([rune_template, item_template])
    db_session.flush()

    item = ItemInstance(template_id=item_template.id, owner_hero_id=owner_id, equipped_slot=None)
    rune_instance = RuneInstance(template_id=rune_template.id, owner_hero_id=owner_id, quantity=1)
    db_session.add_all([item, rune_instance])
    db_session.flush()

    response = client.post(
        f"/api/v1/inventory/{item.id}/apply-rune/{rune_instance.id}", headers=_auth(intruder_token)
    )
    assert response.status_code == 403


def test_apply_rune_api_returns_409_when_item_already_runed(client, db_session):
    token = _signup(client, email="rune-conflict@test.com")
    hero_id = _hero_id(client, token)

    first_rune = RuneTemplate(slug="c-first", name="Conflict First", stat_bonuses={"strength": 1})
    second_rune = RuneTemplate(slug="c-second", name="Conflict Second", stat_bonuses={"strength": 1})
    item_template = ItemTemplate(
        slug="test-conflict-sword", name="Test Sword 5", slot=EquipmentSlot.WEAPON, base_stats={}
    )
    db_session.add_all([first_rune, second_rune, item_template])
    db_session.flush()

    item = ItemInstance(
        template_id=item_template.id,
        owner_hero_id=hero_id,
        equipped_slot=None,
        rune_template_id=first_rune.id,
    )
    second_instance = RuneInstance(template_id=second_rune.id, owner_hero_id=hero_id, quantity=1)
    db_session.add_all([item, second_instance])
    db_session.flush()

    response = client.post(
        f"/api/v1/inventory/{item.id}/apply-rune/{second_instance.id}", headers=_auth(token)
    )
    assert response.status_code == 409


def test_inventory_out_reflects_applied_rune(client, db_session):
    token = _signup(client, email="rune-inventory@test.com")
    hero_id = _hero_id(client, token)

    rune_template = RuneTemplate(slug="display-rune", name="Display Rune", stat_bonuses={"vitality": 2})
    item_template = ItemTemplate(
        slug="test-display-sword", name="Test Sword 6", slot=EquipmentSlot.WEAPON, base_stats={}
    )
    db_session.add_all([rune_template, item_template])
    db_session.flush()

    item = ItemInstance(
        template_id=item_template.id,
        owner_hero_id=hero_id,
        equipped_slot=EquipmentSlot.WEAPON,
        rune_template_id=rune_template.id,
    )
    db_session.add(item)
    db_session.flush()

    body = client.get("/api/v1/inventory", headers=_auth(token)).json()
    assert len(body) == 1
    assert body[0]["rune_name"] == "Display Rune"
    assert body[0]["rune_stat_bonuses"] == {"vitality": 2}


# --- backpack capacity --------------------------------------------------------


def test_backpack_capacity_counts_unattached_rune_stacks(db_session, hero_factory):
    hero = hero_factory()
    rune_template = RuneTemplate(slug="cap-rune", name="Capacity Rune", stat_bonuses={"strength": 1})
    db_session.add(rune_template)
    db_session.flush()
    db_session.add(RuneInstance(template_id=rune_template.id, owner_hero_id=hero.id, quantity=3))
    db_session.flush()

    assert hero_service.get_backpack_used_capacity(db_session, hero) == 3


# --- Forge crafting ------------------------------------------------------------


def test_forge_recipe_craft_grants_a_rune_stack(client, db_session):
    token = _signup(client, email="forge-craft@test.com")
    hero_id = _hero_id(client, token)
    recipe, material, rune = _make_rune_recipe(db_session, slug="forge-recipe-1", quantity_required=3)
    db_session.add(MaterialInstance(template_id=material.id, owner_hero_id=hero_id, quantity=5))
    db_session.flush()

    response = client.post("/api/v1/crafting/craft/forge-recipe-1", headers=_auth(token))
    assert response.status_code == 200
    body = response.json()
    assert body["output_type"] == "rune"
    assert body["rune"]["name"] == rune.name
    assert body["rune"]["quantity"] == 1
    assert body["consumable"] is None

    runes = client.get("/api/v1/runes", headers=_auth(token)).json()
    assert len(runes) == 1
    assert runes[0]["slug"] == rune.slug


def test_recipes_endpoint_filters_by_category(client, db_session):
    token = _signup(client, email="forge-filter@test.com")
    _make_rune_recipe(db_session, slug="forge-recipe-2")

    from app.models.consumable import ConsumableTemplate

    alchemy_material = MaterialTemplate(slug="alchemy-mat", name="Alchemy Mat")
    alchemy_consumable = ConsumableTemplate(slug="alchemy-brew", name="Alchemy Brew", heal_flat=1)
    db_session.add_all([alchemy_material, alchemy_consumable])
    db_session.flush()
    alchemy_recipe = CraftingRecipe(
        slug="alchemy-recipe-1",
        name="Alchemy Recipe 1",
        category=CraftingCategory.ALCHEMY,
        level_requirement=1,
        output_consumable_template_id=alchemy_consumable.id,
        output_quantity=1,
    )
    db_session.add(alchemy_recipe)
    db_session.flush()
    db_session.add(
        CraftingRecipeIngredient(
            recipe_id=alchemy_recipe.id, material_template_id=alchemy_material.id, quantity_required=1
        )
    )
    db_session.flush()

    forge_only = client.get("/api/v1/crafting/recipes?category=forge", headers=_auth(token)).json()
    assert {r["slug"] for r in forge_only} == {"forge-recipe-2"}

    alchemy_only = client.get("/api/v1/crafting/recipes?category=alchemy", headers=_auth(token)).json()
    assert {r["slug"] for r in alchemy_only} == {"alchemy-recipe-1"}

    everything = client.get("/api/v1/crafting/recipes", headers=_auth(token)).json()
    assert {r["slug"] for r in everything} == {"forge-recipe-2", "alchemy-recipe-1"}
