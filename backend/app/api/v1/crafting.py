from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.db import get_db
from app.models.crafting import CraftingCategory
from app.models.material import MaterialInstance
from app.models.user import User
from app.schemas.crafting import CraftingRecipeOut, CraftResultOut
from app.schemas.crafting import craft_result_to_out
from app.schemas.crafting import to_out as recipe_to_out
from app.services import crafting_service

router = APIRouter(prefix="/crafting", tags=["crafting"])


def _owned_materials_by_template(db: Session, hero_id) -> dict:
    rows = db.execute(
        select(MaterialInstance.template_id, func.sum(MaterialInstance.quantity))
        .where(MaterialInstance.owner_hero_id == hero_id)
        .group_by(MaterialInstance.template_id)
    ).all()
    return {template_id: int(total) for template_id, total in rows}


@router.get("/recipes", response_model=list[CraftingRecipeOut])
def get_recipes(
    category: CraftingCategory | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[CraftingRecipeOut]:
    recipes = crafting_service.list_recipes(db, category=category)
    owned = _owned_materials_by_template(db, current_user.hero.id)
    return [recipe_to_out(recipe, current_user.hero, owned) for recipe in recipes]


@router.post("/craft/{recipe_slug}", response_model=CraftResultOut)
def craft(
    recipe_slug: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CraftResultOut:
    try:
        result = crafting_service.craft(db, current_user.hero, recipe_slug)
    except crafting_service.RecipeNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except crafting_service.CraftingServiceError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return craft_result_to_out(result)
