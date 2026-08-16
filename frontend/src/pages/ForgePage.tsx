import { useCallback, useEffect, useState } from "react";
import { craftRecipe, getRecipes } from "../api/alchemy";
import { ApiError } from "../api/client";
import type { CraftingRecipeOut } from "../api/types";
import { useAuth } from "../auth/AuthContext";
import { RecipeOutputIcon } from "../components/RecipeOutputIcon";

type State =
  | { kind: "loading" }
  | { kind: "loaded"; recipes: CraftingRecipeOut[] }
  | { kind: "error"; message: string };

export function ForgePage() {
  const { token } = useAuth();
  const [state, setState] = useState<State>({ kind: "loading" });
  const [pendingSlug, setPendingSlug] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!token) return;
    setState({ kind: "loading" });
    try {
      const recipes = await getRecipes(token, "forge");
      setState({ kind: "loaded", recipes });
    } catch (err) {
      setState({
        kind: "error",
        message: err instanceof ApiError ? err.message : "Failed to load the forge.",
      });
    }
  }, [token]);

  useEffect(() => {
    load();
  }, [load]);

  async function handleForge(recipeSlug: string) {
    if (!token) return;
    setActionError(null);
    setPendingSlug(recipeSlug);
    try {
      await craftRecipe(token, recipeSlug);
      await load();
    } catch (err) {
      setActionError(err instanceof ApiError ? err.message : "Failed to forge that rune.");
    } finally {
      setPendingSlug(null);
    }
  }

  return (
    <div className="page">
      <h1>Forge</h1>
      {state.kind === "loading" && <p>Stoking the coals…</p>}
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
                <li key={recipe.id} className="list-row">
                  <RecipeOutputIcon
                    outputType={recipe.output_type}
                    slug={recipe.output_slug}
                    name={recipe.output_name}
                  />
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
                      onClick={() => handleForge(recipe.slug)}
                    >
                      Forge
                    </button>
                  </span>
                </li>
              ))}
            </ul>
          )}
          <p className="backpack-panel-empty">Forged runes go straight to your Backpack.</p>
        </>
      )}
    </div>
  );
}
