import { useCallback, useEffect, useState } from "react";
import { ApiError } from "../api/client";
import { getMaterials, sellMaterial } from "../api/materials";
import type { CraftingCategory, MaterialInstanceOut } from "../api/types";
import { useAuth } from "../auth/AuthContext";
import { MaterialIcon } from "../components/MaterialIcon";

type State =
  | { kind: "loading" }
  | { kind: "loaded"; materials: MaterialInstanceOut[] }
  | { kind: "error"; message: string };

export function MaterialsPage() {
  const { token, refetch } = useAuth();
  const [state, setState] = useState<State>({ kind: "loading" });
  const [pendingId, setPendingId] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!token) return;
    setState({ kind: "loading" });
    try {
      const materials = await getMaterials(token);
      setState({ kind: "loaded", materials });
    } catch (err) {
      setState({
        kind: "error",
        message: err instanceof ApiError ? err.message : "Failed to load materials.",
      });
    }
  }, [token]);

  useEffect(() => {
    load();
  }, [load]);

  async function handleSell(materialId: string) {
    if (!token) return;
    setActionError(null);
    setPendingId(materialId);
    try {
      await sellMaterial(token, materialId);
      await Promise.all([load(), refetch()]);
    } catch (err) {
      setActionError(err instanceof ApiError ? err.message : "Failed to sell that material.");
    } finally {
      setPendingId(null);
    }
  }

  return (
    <div className="page">
      <h1>Materials</h1>
      {state.kind === "loading" && <p>Sifting through gathered materials…</p>}
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

          {MATERIAL_PANELS.map(({ category, label }) => {
            const categoryMaterials = state.materials.filter((m) => m.category === category);
            return (
              <details key={category} className="backpack-panel" open>
                <summary className="backpack-panel-summary">
                  {label} ({categoryMaterials.length})
                </summary>
                {categoryMaterials.length === 0 ? (
                  <p className="backpack-panel-empty">No {label.toLowerCase()}.</p>
                ) : (
                  <ul className="equipment-list">
                    {categoryMaterials.map((material) => (
                      <li key={material.id} className="list-row">
                        <span className="equipment-slot-label">{material.name}</span>
                        <MaterialIcon slug={material.slug} name={material.name} />
                        <span className="equipment-slot-filled">
                          <span className="equipment-slot-value">×{material.quantity}</span>
                          <button
                            type="button"
                            className="small-button"
                            disabled={pendingId === material.id}
                            onClick={() => handleSell(material.id)}
                          >
                            Sell ({Math.round(material.price * 0.25)}g)
                          </button>
                        </span>
                      </li>
                    ))}
                  </ul>
                )}
              </details>
            );
          })}
        </>
      )}
    </div>
  );
}

const MATERIAL_PANELS: { category: CraftingCategory; label: string }[] = [
  { category: "alchemy", label: "Alchemy Reagents" },
  { category: "forge", label: "Forging Materials" },
];
