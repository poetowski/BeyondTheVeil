import { useCallback, useEffect, useState } from "react";
import { ApiError } from "../api/client";
import { getMaterials } from "../api/materials";
import type { MaterialInstanceOut } from "../api/types";
import { useAuth } from "../auth/AuthContext";

type State =
  | { kind: "loading" }
  | { kind: "loaded"; materials: MaterialInstanceOut[] }
  | { kind: "error"; message: string };

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
          {state.materials.length === 0 ? (
            <p>You haven't gathered any materials yet.</p>
          ) : (
            <ul className="equipment-list">
              {state.materials.map((material) => (
                <li key={material.id}>
                  <span className="equipment-slot-label">{material.name}</span>
                  <span className="equipment-slot-value">×{material.quantity}</span>
                </li>
              ))}
            </ul>
          )}
        </>
      )}
    </div>
  );
}
