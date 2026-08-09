import { apiFetch } from "./client";
import type { ConsumableInstanceOut, CraftingRecipeOut, HeroOut } from "./types";

export function getRecipes(token: string): Promise<CraftingRecipeOut[]> {
  return apiFetch<CraftingRecipeOut[]>("/api/v1/crafting/recipes", { token });
}

export function craftRecipe(token: string, recipeSlug: string): Promise<ConsumableInstanceOut> {
  return apiFetch<ConsumableInstanceOut>(`/api/v1/crafting/craft/${recipeSlug}`, {
    method: "POST",
    token,
  });
}

export function getConsumables(token: string): Promise<ConsumableInstanceOut[]> {
  return apiFetch<ConsumableInstanceOut[]>("/api/v1/consumables", { token });
}

export function useConsumable(token: string, consumableId: string): Promise<HeroOut> {
  return apiFetch<HeroOut>(`/api/v1/consumables/${consumableId}/use`, {
    method: "POST",
    token,
  });
}
