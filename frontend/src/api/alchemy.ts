import { apiFetch } from "./client";
import type {
  ConsumableInstanceOut,
  CraftingCategory,
  CraftingRecipeOut,
  CraftResultOut,
  HeroOut,
  SellResultOut,
} from "./types";

export function getRecipes(token: string, category?: CraftingCategory): Promise<CraftingRecipeOut[]> {
  const query = category ? `?category=${category}` : "";
  return apiFetch<CraftingRecipeOut[]>(`/api/v1/crafting/recipes${query}`, { token });
}

export function craftRecipe(token: string, recipeSlug: string): Promise<CraftResultOut> {
  return apiFetch<CraftResultOut>(`/api/v1/crafting/craft/${recipeSlug}`, {
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

export function sellConsumable(token: string, consumableId: string): Promise<SellResultOut> {
  return apiFetch<SellResultOut>(`/api/v1/consumables/${consumableId}/sell`, {
    method: "POST",
    token,
  });
}
