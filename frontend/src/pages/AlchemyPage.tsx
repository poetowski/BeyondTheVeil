import { useCallback, useEffect, useState } from "react";
import { craftRecipe, getRecipes } from "../api/alchemy";
import { ApiError } from "../api/client";
import type { CraftingRecipeOut } from "../api/types";
import { useAuth } from "../auth/AuthContext";

type State =
  | { kind: "loading" }
  | { kind: "loaded"; recipes: CraftingRecipeOut[] }
  | { kind: "error"; message: string };

export function AlchemyPage() {
  const { token } = useAuth();
  const [state, setState] = useState<State>({ kind: "loading" });
  const [pendingSlug, setPendingSlug] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!token) return;
    setState({ kind: "loading" });
    try {
      const recipes = await getRecipes(token);
      setState({ kind: "loaded", recipes });
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
    setPendingSlug(recipeSlug);
    try {
      await craftRecipe(token, recipeSlug);
      await load();
    } catch (err) {
      setActionError(err instanceof ApiError ? err.message : "Failed to brew that recipe.");
    } finally {
      setPendingSlug(null);
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
                      disabled={!recipe.craftable || pendingSlug === recipe.slug}
                      onClick={() => handleBrew(recipe.slug)}
                    >
                      Brew
                    </button>
                  </span>
                </li>
              ))}
            </ul>
          )}
          <p className="backpack-panel-empty">Brewed elixirs go straight to your Backpack.</p>
        </>
      )}
    </div>
  );
}
