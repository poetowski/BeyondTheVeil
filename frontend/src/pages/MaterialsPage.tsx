import { useCallback, useEffect, useState } from "react";
import { ApiError } from "../api/client";
import { getMaterials } from "../api/materials";
import type { CraftingCategory, MaterialInstanceOut } from "../api/types";
import { useAuth } from "../auth/AuthContext";

type State =
  | { kind: "loading" }
  | { kind: "loaded"; materials: MaterialInstanceOut[] }
  | { kind: "error"; message: string };

function MaterialIcon({ material }: { material: MaterialInstanceOut }) {
  const [missing, setMissing] = useState(false);
  if (missing) {
    return <div className="material-icon material-icon--missing" aria-hidden="true" />;
  }
  return (
    <img
      className="material-icon"
      src={`/materials/${material.slug}.svg`}
      alt={material.name}
      onError={() => setMissing(true)}
    />
  );
}

export function MaterialsPage() {
  const { token } = useAuth();
  const [state, setState] = useState<State>({ kind: "loading" });

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
                      <li key={material.id} className="material-row">
                        <span className="equipment-slot-label">{material.name}</span>
                        <MaterialIcon material={material} />
                        <span className="equipment-slot-value">×{material.quantity}</span>
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
