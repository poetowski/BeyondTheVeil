import uuid

from pydantic import BaseModel

from app.models.crafting import CraftingCategory, CraftingRecipe
from app.models.hero import Hero


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
    output_consumable_name: str
    output_quantity: int
    ingredients: list[RecipeIngredientOut]
    craftable: bool


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

    return CraftingRecipeOut(
        id=recipe.id,
        slug=recipe.slug,
        name=recipe.name,
        category=recipe.category,
        level_requirement=recipe.level_requirement,
        output_consumable_name=recipe.output_consumable_template.name,
        output_quantity=recipe.output_quantity,
        ingredients=ingredients,
        craftable=craftable,
    )
