import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.consumable import ConsumableInstance
from app.models.crafting import CraftingCategory, CraftingRecipe
from app.models.hero import Hero
from app.models.item import ItemInstance
from app.models.material import MaterialInstance
from app.models.rune import RuneInstance
from app.services import hero_service


class CraftingServiceError(Exception):
    """Base class for crafting/consumable failures."""


class RecipeNotFoundError(CraftingServiceError):
    pass


class LevelRequirementNotMetError(CraftingServiceError):
    pass


class InsufficientMaterialsError(CraftingServiceError):
    pass


class InventoryFullError(CraftingServiceError):
    pass


class ConsumableNotFoundError(CraftingServiceError):
    pass


class ConsumableNotOwnedError(CraftingServiceError):
    pass


@dataclass
class CraftResult:
    consumable: ConsumableInstance | None
    rune: RuneInstance | None
    item: ItemInstance | None


def list_recipes(db: Session, category: CraftingCategory | None = None) -> list[CraftingRecipe]:
    stmt = select(CraftingRecipe).order_by(CraftingRecipe.slug)
    if category is not None:
        stmt = stmt.where(CraftingRecipe.category == category)
    return db.execute(stmt).scalars().all()


def craft(db: Session, hero: Hero, recipe_slug: str) -> CraftResult:
    """Deducts a recipe's required materials and grants its output consumable.

    Verifies every ingredient is affordable *before* deducting any of them
    (two-pass: verify-then-deduct), so a shortfall discovered partway
    through never leaves materials partially spent without the promised
    output.
    """
    recipe = db.execute(
        select(CraftingRecipe).where(CraftingRecipe.slug == recipe_slug)
    ).scalar_one_or_none()
    if recipe is None:
        raise RecipeNotFoundError(f"recipe {recipe_slug!r} not found")
    if hero.level < recipe.level_requirement:
        raise LevelRequirementNotMetError("hero level is too low for this recipe")

    used_capacity = hero_service.get_backpack_used_capacity(db, hero)
    if used_capacity + recipe.output_quantity > hero.inventory_capacity:
        raise InventoryFullError("not enough backpack space to hold the result")

    owned_by_template: dict[uuid.UUID, list[MaterialInstance]] = {}
    for ingredient in recipe.ingredients:
        stacks = (
            db.execute(
                select(MaterialInstance).where(
                    MaterialInstance.owner_hero_id == hero.id,
                    MaterialInstance.template_id == ingredient.material_template_id,
                )
            )
            .scalars()
            .all()
        )
        owned_by_template[ingredient.material_template_id] = stacks
        total_owned = sum(stack.quantity for stack in stacks)
        if total_owned < ingredient.quantity_required:
            raise InsufficientMaterialsError(
                f"not enough {ingredient.material_template.name} "
                f"(need {ingredient.quantity_required}, have {total_owned})"
            )

    for ingredient in recipe.ingredients:
        remaining = ingredient.quantity_required
        for stack in owned_by_template[ingredient.material_template_id]:
            if remaining <= 0:
                break
            take = min(stack.quantity, remaining)
            stack.quantity -= take
            remaining -= take
            if stack.quantity == 0:
                db.delete(stack)
            else:
                db.add(stack)

    if recipe.output_item_template_id is not None:
        # Items never stack (no quantity column on ItemInstance, unlike
        # runes/consumables/materials) - craft one row per unit.
        item_result: ItemInstance | None = None
        for _ in range(recipe.output_quantity):
            item_result = ItemInstance(
                template_id=recipe.output_item_template_id,
                owner_hero_id=hero.id,
            )
            db.add(item_result)

        db.commit()
        db.refresh(item_result)
        return CraftResult(consumable=None, rune=None, item=item_result)

    if recipe.output_rune_template_id is not None:
        existing_rune = (
            db.execute(
                select(RuneInstance).where(
                    RuneInstance.owner_hero_id == hero.id,
                    RuneInstance.template_id == recipe.output_rune_template_id,
                )
            )
            .scalars()
            .first()
        )
        if existing_rune is not None:
            existing_rune.quantity += recipe.output_quantity
            db.add(existing_rune)
            rune_result = existing_rune
        else:
            rune_result = RuneInstance(
                template_id=recipe.output_rune_template_id,
                owner_hero_id=hero.id,
                quantity=recipe.output_quantity,
            )
            db.add(rune_result)

        db.commit()
        db.refresh(rune_result)
        return CraftResult(consumable=None, rune=rune_result, item=None)

    existing_consumable = (
        db.execute(
            select(ConsumableInstance).where(
                ConsumableInstance.owner_hero_id == hero.id,
                ConsumableInstance.template_id == recipe.output_consumable_template_id,
            )
        )
        .scalars()
        .first()
    )
    if existing_consumable is not None:
        existing_consumable.quantity += recipe.output_quantity
        db.add(existing_consumable)
        consumable_result = existing_consumable
    else:
        consumable_result = ConsumableInstance(
            template_id=recipe.output_consumable_template_id,
            owner_hero_id=hero.id,
            quantity=recipe.output_quantity,
        )
        db.add(consumable_result)

    db.commit()
    db.refresh(consumable_result)
    return CraftResult(consumable=consumable_result, rune=None, item=None)


def use_consumable(db: Session, hero: Hero, consumable_instance_id: uuid.UUID) -> Hero:
    """Applies a consumable's heal effect immediately (a synchronous action,
    not a delayed veil-run outcome, so there's no entry/claim split to
    respect here - current_hp/hp_updated_at are written right away)."""
    consumable = db.get(ConsumableInstance, consumable_instance_id)
    if consumable is None:
        raise ConsumableNotFoundError(f"consumable {consumable_instance_id} not found")
    if consumable.owner_hero_id != hero.id:
        raise ConsumableNotOwnedError("hero does not own this consumable")

    equipped_items = hero_service.get_equipped_items(db, hero)
    effective_stats = hero_service.compute_effective_stats(hero, equipped_items)
    bonus_max_hp = hero_service.compute_bonus_max_hp(equipped_items)
    max_hp = hero_service.compute_max_hp(effective_stats["vitality"], bonus_max_hp)
    current_hp = hero_service.compute_current_hp(
        hero, effective_stats["vitality"], bonus_max_hp=bonus_max_hp
    )
    heal_amount = round(
        consumable.template.heal_flat
        + consumable.template.heal_vitality_multiplier * effective_stats["vitality"]
    )

    hero.current_hp = min(max_hp, current_hp + heal_amount)
    hero.hp_updated_at = datetime.now(timezone.utc)
    db.add(hero)

    consumable.quantity -= 1
    if consumable.quantity == 0:
        db.delete(consumable)
    else:
        db.add(consumable)

    db.commit()
    db.refresh(hero)
    return hero
