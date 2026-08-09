import { useCallback, useEffect, useState } from "react";
import { craftRecipe, getConsumables, getRecipes, useConsumable as consumeConsumable } from "../api/alchemy";
import { ApiError } from "../api/client";
import type { ConsumableInstanceOut, CraftingRecipeOut } from "../api/types";
import { useAuth } from "../auth/AuthContext";

type State =
  | { kind: "loading" }
  | { kind: "loaded"; recipes: CraftingRecipeOut[]; consumables: ConsumableInstanceOut[] }
  | { kind: "error"; message: string };

export function AlchemyPage() {
  const { token, refetch } = useAuth();
  const [state, setState] = useState<State>({ kind: "loading" });
  const [pendingId, setPendingId] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!token) return;
    setState({ kind: "loading" });
    try {
      const [recipes, consumables] = await Promise.all([getRecipes(token), getConsumables(token)]);
      setState({ kind: "loaded", recipes, consumables });
    } catch (err) {
      setState({
        kind: "error",
        message: err instanceof ApiError ? err.message : "Failed to load the alchemy lab.",
      });
    }
  }, [token]);

  useEffect(() => {
    load();
  }, [load]);

  async function handleBrew(recipeSlug: string) {
    if (!token) return;
    setActionError(null);
    setPendingId(recipeSlug);
    try {
      await craftRecipe(token, recipeSlug);
      await load();
    } catch (err) {
      setActionError(err instanceof ApiError ? err.message : "Failed to brew that recipe.");
    } finally {
      setPendingId(null);
    }
  }

  async function handleUse(consumableId: string) {
    if (!token) return;
    setActionError(null);
    setPendingId(consumableId);
    try {
      await consumeConsumable(token, consumableId);
      await Promise.all([load(), refetch()]);
    } catch (err) {
      setActionError(err instanceof ApiError ? err.message : "Failed to use that item.");
    } finally {
      setPendingId(null);
    }
  }

  return (
    <div className="page">
      <h1>Alchemy</h1>
      {state.kind === "loading" && <p>Warming the crucible…</p>}
      {state.kind === "error" && (
        <>
          <p className="auth-error">{state.message}</p>
          <button type="button" onClick={load}>
            Retry
          </button>
        </>
      )}
      {state.kind === "loaded" && (
        <>
          {actionError && <p className="auth-error">{actionError}</p>}

          <h2>Recipes</h2>
          {state.recipes.length === 0 ? (
            <p>No recipes known yet.</p>
          ) : (
            <ul className="equipment-list">
              {state.recipes.map((recipe) => (
                <li key={recipe.id}>
                  <span className="equipment-slot-label">{recipe.name}</span>
                  <span className="equipment-slot-filled">
                    <span className="equipment-slot-value">
                      {recipe.ingredients
                        .map((i) => `${i.material_name} ${i.quantity_owned}/${i.quantity_required}`)
                        .join(", ")}
                    </span>
                    <button
                      type="button"
                      className="small-button"
                      disabled={!recipe.craftable || pendingId === recipe.slug}
                      onClick={() => handleBrew(recipe.slug)}
                    >
                      Brew
                    </button>
                  </span>
                </li>
              ))}
            </ul>
          )}

          <h2>Your Elixirs</h2>
          {state.consumables.length === 0 ? (
            <p>You aren't carrying any elixirs.</p>
          ) : (
            <ul className="equipment-list">
              {state.consumables.map((consumable) => (
                <li key={consumable.id}>
                  <span className="equipment-slot-label">{consumable.name}</span>
                  <span className="equipment-slot-filled">
                    <span className="equipment-slot-value">×{consumable.quantity}</span>
                    <button
                      type="button"
                      className="small-button"
                      disabled={pendingId === consumable.id}
                      onClick={() => handleUse(consumable.id)}
                    >
                      Use
                    </button>
                  </span>
                </li>
              ))}
            </ul>
          )}
        </>
      )}
    </div>
  );
}
