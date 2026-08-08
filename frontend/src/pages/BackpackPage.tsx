import { useCallback, useEffect, useState } from "react";
import { ApiError } from "../api/client";
import { getInventory } from "../api/inventory";
import type { ItemInstanceOut } from "../api/types";
import { useAuth } from "../auth/AuthContext";

type State =
  | { kind: "loading" }
  | { kind: "loaded"; items: ItemInstanceOut[] }
  | { kind: "error"; message: string };

export function BackpackPage() {
  const { token } = useAuth();
  const [state, setState] = useState<State>({ kind: "loading" });

  const load = useCallback(async () => {
    if (!token) return;
    setState({ kind: "loading" });
    try {
      const items = await getInventory(token);
      setState({ kind: "loaded", items });
    } catch (err) {
      setState({
        kind: "error",
        message: err instanceof ApiError ? err.message : "Failed to load the backpack.",
      });
    }
  }, [token]);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <div className="page">
      <h1>Backpack</h1>
      {state.kind === "loading" && <p>Rummaging through the backpack…</p>}
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
          {state.items.length === 0 ? (
            <p>Your backpack is empty.</p>
          ) : (
            <ul className="equipment-list">
              {state.items.map((item) => (
                <li key={item.id}>
                  <span className="equipment-slot-label">{item.name}</span>
                  <span className="equipment-slot-value">
                    {item.rarity} · {item.slot}
                    {item.equipped_slot !== null ? " · equipped" : ""}
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
