import uuid
from typing import Literal

from pydantic import BaseModel

from app.models.crafting import CraftingCategory, CraftingRecipe
from app.models.hero import Hero
from app.schemas.consumable import ConsumableInstanceOut
from app.schemas.consumable import to_out as consumable_to_out
from app.schemas.rune import RuneInstanceOut
from app.schemas.rune import to_out as rune_to_out
from app.services.crafting_service import CraftResult


class RecipeIngredientOut(BaseModel):
    material_name: str
    material_template_slug: str
    quantity_required: int
    quantity_owned: int


class CraftingRecipeOut(BaseModel):
    id: uuid.UUID
    slug: str
    name: str
    category: CraftingCategory
    level_requirement: int
    output_name: str
    output_type: Literal["consumable", "rune"]
    output_quantity: int
    ingredients: list[RecipeIngredientOut]
    craftable: bool


class CraftResultOut(BaseModel):
    output_type: Literal["consumable", "rune"]
    consumable: ConsumableInstanceOut | None
    rune: RuneInstanceOut | None


def to_out(
    recipe: CraftingRecipe, hero: Hero, owned_materials_by_template: dict[uuid.UUID, int]
) -> CraftingRecipeOut:
    ingredients = []
    craftable = hero.level >= recipe.level_requirement
    for ingredient in recipe.ingredients:
        quantity_owned = owned_materials_by_template.get(ingredient.material_template_id, 0)
        if quantity_owned < ingredient.quantity_required:
            craftable = False
        ingredients.append(
            RecipeIngredientOut(
                material_name=ingredient.material_template.name,
                material_template_slug=ingredient.material_template.slug,
                quantity_required=ingredient.quantity_required,
                quantity_owned=quantity_owned,
            )
        )

    if recipe.output_rune_template_id is not None:
        output_type: Literal["consumable", "rune"] = "rune"
        output_name = recipe.output_rune_template.name
    else:
        output_type = "consumable"
        output_name = recipe.output_consumable_template.name

    return CraftingRecipeOut(
        id=recipe.id,
        slug=recipe.slug,
        name=recipe.name,
        category=recipe.category,
        level_requirement=recipe.level_requirement,
        output_name=output_name,
        output_type=output_type,
        output_quantity=recipe.output_quantity,
        ingredients=ingredients,
        craftable=craftable,
    )


def craft_result_to_out(result: CraftResult) -> CraftResultOut:
    if result.rune is not None:
        return CraftResultOut(output_type="rune", consumable=None, rune=rune_to_out(result.rune))
    return CraftResultOut(
        output_type="consumable", consumable=consumable_to_out(result.consumable), rune=None
    )
