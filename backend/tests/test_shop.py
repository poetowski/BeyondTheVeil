import uuid
from datetime import date

from app.models.consumable import ConsumableInstance, ConsumableTemplate
from app.models.hero import Hero
from app.models.item import EquipmentSlot, ItemInstance, ItemTemplate
from app.models.material import MaterialInstance, MaterialTemplate
from app.models.rune import RuneInstance, RuneTemplate
from app.services import hero_service, shop_service


def _signup(client, email="shop@test.com", hero_name="Merchant"):
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


def _make_item_templates(db_session, count, *, price=100, prefix="shop-item"):
    templates = []
    for i in range(count):
        template = ItemTemplate(
            slug=f"{prefix}-{i}", name=f"Shop Item {i}", slot=EquipmentSlot.WEAPON, price=price
        )
        db_session.add(template)
        templates.append(template)
    db_session.flush()
    return templates


def _make_material_templates(db_session, count, *, price=10, prefix="shop-material"):
    templates = []
    for i in range(count):
        template = MaterialTemplate(slug=f"{prefix}-{i}", name=f"Shop Material {i}", price=price)
        db_session.add(template)
        templates.append(template)
    db_session.flush()
    return templates


def _make_standard_pool(db_session, *, item_price=100, material_price=10):
    """4 item templates + 2 material templates - matches the real
    GEAR_SLOT_COUNT/MATERIAL_SLOT_COUNT shape so every roll fills all 6 slots."""
    items = _make_item_templates(db_session, 4, price=item_price)
    materials = _make_material_templates(db_session, 2, price=material_price)
    return items, materials


# --- roll determinism ---------------------------------------------------


def test_roll_daily_shop_is_identical_across_repeated_calls(db_session, hero_factory):
    hero = hero_factory()
    _make_standard_pool(db_session, item_price=140, material_price=28)

    d = date(2026, 1, 1)
    first = shop_service.roll_daily_shop(db_session, hero, d)
    second = shop_service.roll_daily_shop(db_session, hero, d)

    first_ids = [(s.slot_index, s.slot_type, s.template.id) for s in first]
    second_ids = [(s.slot_index, s.slot_type, s.template.id) for s in second]
    assert first_ids == second_ids


def test_roll_daily_shop_produces_four_gear_and_two_material_slots(db_session, hero_factory):
    hero = hero_factory()
    _make_standard_pool(db_session)

    slots = shop_service.roll_daily_shop(db_session, hero, date(2026, 1, 1))

    item_slots = [s for s in slots if s.slot_type == "item"]
    material_slots = [s for s in slots if s.slot_type == "material"]
    assert len(item_slots) == shop_service.GEAR_SLOT_COUNT
    assert len(material_slots) == shop_service.MATERIAL_SLOT_COUNT
    assert sorted(s.slot_index for s in slots) == list(range(shop_service.TOTAL_SLOT_COUNT))


def test_roll_daily_shop_differs_by_date(db_session, hero_factory):
    hero = hero_factory()
    # Oversized pool (more templates than slots) so the sampled subset/order
    # can actually vary between rolls.
    _make_item_templates(db_session, 10, price=100)
    _make_material_templates(db_session, 10, price=10)

    slots_day_1 = shop_service.roll_daily_shop(db_session, hero, date(2026, 1, 1))
    slots_day_2 = shop_service.roll_daily_shop(db_session, hero, date(2026, 1, 2))

    ids_1 = [s.template.id for s in slots_day_1]
    ids_2 = [s.template.id for s in slots_day_2]
    assert ids_1 != ids_2


def test_roll_daily_shop_differs_by_hero(db_session, hero_factory):
    hero_a = hero_factory()
    hero_b = hero_factory()
    _make_item_templates(db_session, 10, price=100)
    _make_material_templates(db_session, 10, price=10)

    d = date(2026, 1, 1)
    assert shop_service._shop_seed(hero_a.id, d) != shop_service._shop_seed(hero_b.id, d)

    ids_a = [s.template.id for s in shop_service.roll_daily_shop(db_session, hero_a, d)]
    ids_b = [s.template.id for s in shop_service.roll_daily_shop(db_session, hero_b, d)]
    assert ids_a != ids_b


# --- buy flow -------------------------------------------------------------


def test_buy_slot_grants_item_and_deducts_gold(client, db_session):
    token = _signup(client, email="buy-item@test.com")
    hero_id = _hero_id(client, token)
    hero = db_session.get(Hero, hero_id)
    hero.gold = 1000
    db_session.flush()
    _make_standard_pool(db_session, item_price=140)

    response = client.post("/api/v1/shop/buy/0", headers=_auth(token))
    assert response.status_code == 200
    body = response.json()
    assert body["slot_type"] == "item"
    assert body["item"] is not None
    assert body["gold_spent"] == 140

    db_session.expire_all()
    hero = db_session.get(Hero, hero_id)
    assert hero.gold == 1000 - 140
    items = db_session.query(ItemInstance).filter_by(owner_hero_id=hero_id).all()
    assert len(items) == 1


def test_buy_slot_grants_material_and_stacks_existing(client, db_session):
    token = _signup(client, email="buy-material@test.com")
    hero_id = _hero_id(client, token)
    hero = db_session.get(Hero, hero_id)
    hero.gold = 1000
    db_session.flush()
    _, materials = _make_standard_pool(db_session, material_price=28)

    # Pre-own a stack of whichever material lands in slot 4, so we can
    # confirm buying stacks onto it instead of creating a second row.
    slot_4_template_id = shop_service.roll_daily_shop(db_session, hero, shop_service.today_utc())[4].template.id
    existing = MaterialInstance(template_id=slot_4_template_id, owner_hero_id=hero_id, quantity=3)
    db_session.add(existing)
    db_session.flush()

    response = client.post("/api/v1/shop/buy/4", headers=_auth(token))
    assert response.status_code == 200
    body = response.json()
    assert body["slot_type"] == "material"
    assert body["material"]["quantity"] == 4

    stacks = db_session.query(MaterialInstance).filter_by(owner_hero_id=hero_id).all()
    assert len(stacks) == 1


def test_buy_slot_twice_same_day_rejects_second_attempt(client, db_session):
    token = _signup(client, email="buy-twice@test.com")
    hero_id = _hero_id(client, token)
    hero = db_session.get(Hero, hero_id)
    hero.gold = 1000
    db_session.flush()
    _make_standard_pool(db_session)

    first = client.post("/api/v1/shop/buy/0", headers=_auth(token))
    assert first.status_code == 200
    second = client.post("/api/v1/shop/buy/0", headers=_auth(token))
    assert second.status_code == 409


def test_buy_slot_insufficient_gold_rejects(client, db_session):
    token = _signup(client, email="buy-poor@test.com")
    hero_id = _hero_id(client, token)
    hero = db_session.get(Hero, hero_id)
    hero.gold = 0
    db_session.flush()
    _make_standard_pool(db_session, item_price=140)

    response = client.post("/api/v1/shop/buy/0", headers=_auth(token))
    assert response.status_code == 409


def test_buy_gear_slot_backpack_full_rejects(client, db_session):
    token = _signup(client, email="buy-full@test.com")
    hero_id = _hero_id(client, token)
    hero = db_session.get(Hero, hero_id)
    hero.gold = 1000
    hero.inventory_capacity = 1
    db_session.flush()
    _make_standard_pool(db_session)

    # Fill the single backpack slot with an unrelated item first.
    blocker_template = ItemTemplate(
        slug="shop-full-blocker", name="Blocker", slot=EquipmentSlot.HELMET, price=0
    )
    db_session.add(blocker_template)
    db_session.flush()
    db_session.add(
        ItemInstance(template_id=blocker_template.id, owner_hero_id=hero_id, equipped_slot=None)
    )
    db_session.flush()

    response = client.post("/api/v1/shop/buy/0", headers=_auth(token))
    assert response.status_code == 409


def test_buy_material_slot_ignores_backpack_capacity(client, db_session):
    token = _signup(client, email="buy-full-material@test.com")
    hero_id = _hero_id(client, token)
    hero = db_session.get(Hero, hero_id)
    hero.gold = 1000
    hero.inventory_capacity = 1
    db_session.flush()
    _make_standard_pool(db_session)

    blocker_template = ItemTemplate(
        slug="shop-full-blocker-2", name="Blocker 2", slot=EquipmentSlot.HELMET, price=0
    )
    db_session.add(blocker_template)
    db_session.flush()
    db_session.add(
        ItemInstance(template_id=blocker_template.id, owner_hero_id=hero_id, equipped_slot=None)
    )
    db_session.flush()

    response = client.post("/api/v1/shop/buy/4", headers=_auth(token))
    assert response.status_code == 200


def test_buy_invalid_slot_index_rejects(client, db_session):
    token = _signup(client, email="buy-invalid@test.com")
    _make_standard_pool(db_session)

    response = client.post("/api/v1/shop/buy/6", headers=_auth(token))
    assert response.status_code == 404


def test_get_shop_reflects_already_bought_after_purchase(client, db_session):
    token = _signup(client, email="shop-status@test.com")
    hero_id = _hero_id(client, token)
    hero = db_session.get(Hero, hero_id)
    hero.gold = 1000
    db_session.flush()
    _make_standard_pool(db_session)

    before = client.get("/api/v1/shop", headers=_auth(token)).json()
    assert all(slot["already_bought"] is False for slot in before["slots"])

    client.post("/api/v1/shop/buy/0", headers=_auth(token))

    after = client.get("/api/v1/shop", headers=_auth(token)).json()
    by_index = {slot["slot_index"]: slot for slot in after["slots"]}
    assert by_index[0]["already_bought"] is True
    assert by_index[1]["already_bought"] is False


# --- sell flow --------------------------------------------------------------


def test_sell_item_grants_quarter_price_and_removes_it(client, db_session):
    token = _signup(client, email="sell-item@test.com")
    hero_id = _hero_id(client, token)
    hero = db_session.get(Hero, hero_id)
    hero.gold = 0
    db_session.flush()

    template = ItemTemplate(slug="sell-sword", name="Sell Sword", slot=EquipmentSlot.WEAPON, price=100)
    db_session.add(template)
    db_session.flush()
    item = ItemInstance(template_id=template.id, owner_hero_id=hero_id, equipped_slot=None)
    db_session.add(item)
    db_session.flush()

    response = client.post(f"/api/v1/inventory/{item.id}/sell", headers=_auth(token))
    assert response.status_code == 200
    assert response.json()["gold_gained"] == 25

    db_session.expire_all()
    assert db_session.get(Hero, hero_id).gold == 25
    assert db_session.get(ItemInstance, item.id) is None


def test_sell_equipped_item_is_blocked(client, db_session):
    token = _signup(client, email="sell-equipped@test.com")
    hero_id = _hero_id(client, token)

    template = ItemTemplate(slug="sell-equipped-sword", name="Equipped Sword", slot=EquipmentSlot.WEAPON, price=100)
    db_session.add(template)
    db_session.flush()
    item = ItemInstance(
        template_id=template.id, owner_hero_id=hero_id, equipped_slot=EquipmentSlot.WEAPON
    )
    db_session.add(item)
    db_session.flush()

    response = client.post(f"/api/v1/inventory/{item.id}/sell", headers=_auth(token))
    assert response.status_code == 409


def test_sell_material_decrements_stack_and_deletes_at_zero(client, db_session):
    token = _signup(client, email="sell-material@test.com")
    hero_id = _hero_id(client, token)
    hero = db_session.get(Hero, hero_id)
    hero.gold = 0
    db_session.flush()

    template = MaterialTemplate(slug="sell-mat", name="Sell Mat", price=20)
    db_session.add(template)
    db_session.flush()
    stack = MaterialInstance(template_id=template.id, owner_hero_id=hero_id, quantity=2)
    db_session.add(stack)
    db_session.flush()

    first = client.post(f"/api/v1/materials/{stack.id}/sell", headers=_auth(token))
    assert first.status_code == 200
    assert first.json()["gold_gained"] == 5

    db_session.expire_all()
    remaining = db_session.get(MaterialInstance, stack.id)
    assert remaining.quantity == 1

    second = client.post(f"/api/v1/materials/{stack.id}/sell", headers=_auth(token))
    assert second.status_code == 200

    db_session.expire_all()
    assert db_session.get(MaterialInstance, stack.id) is None
    assert db_session.get(Hero, hero_id).gold == 10


def test_sell_consumable_grants_gold_and_decrements(client, db_session):
    token = _signup(client, email="sell-consumable@test.com")
    hero_id = _hero_id(client, token)
    hero = db_session.get(Hero, hero_id)
    hero.gold = 0
    db_session.flush()

    template = ConsumableTemplate(slug="sell-potion", name="Sell Potion", price=200)
    db_session.add(template)
    db_session.flush()
    stack = ConsumableInstance(template_id=template.id, owner_hero_id=hero_id, quantity=1)
    db_session.add(stack)
    db_session.flush()

    response = client.post(f"/api/v1/consumables/{stack.id}/sell", headers=_auth(token))
    assert response.status_code == 200
    assert response.json()["gold_gained"] == 50

    db_session.expire_all()
    assert db_session.get(ConsumableInstance, stack.id) is None


def test_sell_rune_grants_gold_and_decrements(client, db_session):
    token = _signup(client, email="sell-rune@test.com")
    hero_id = _hero_id(client, token)
    hero = db_session.get(Hero, hero_id)
    hero.gold = 0
    db_session.flush()

    template = RuneTemplate(slug="sell-rune", name="Sell Rune", price=1540)
    db_session.add(template)
    db_session.flush()
    stack = RuneInstance(template_id=template.id, owner_hero_id=hero_id, quantity=1)
    db_session.add(stack)
    db_session.flush()

    response = client.post(f"/api/v1/runes/{stack.id}/sell", headers=_auth(token))
    assert response.status_code == 200
    assert response.json()["gold_gained"] == 385

    db_session.expire_all()
    assert db_session.get(RuneInstance, stack.id) is None


def test_sell_unowned_item_rejects(client, db_session):
    owner_token = _signup(client, email="sell-owner@test.com", hero_name="Owner")
    owner_id = _hero_id(client, owner_token)
    intruder_token = _signup(client, email="sell-intruder@test.com", hero_name="Intruder")

    template = ItemTemplate(slug="guarded-sell-sword", name="Guarded Sword", slot=EquipmentSlot.WEAPON, price=100)
    db_session.add(template)
    db_session.flush()
    item = ItemInstance(template_id=template.id, owner_hero_id=owner_id, equipped_slot=None)
    db_session.add(item)
    db_session.flush()

    response = client.post(f"/api/v1/inventory/{item.id}/sell", headers=_auth(intruder_token))
    assert response.status_code == 403


def test_sell_nonexistent_item_returns_404(client):
    token = _signup(client, email="sell-ghost@test.com")
    response = client.post(f"/api/v1/inventory/{uuid.uuid4()}/sell", headers=_auth(token))
    assert response.status_code == 404
