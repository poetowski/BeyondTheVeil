import { useCallback, useEffect, useState } from "react";
import { ApiError } from "../api/client";
import { equipItem, getInventory, unequipItem } from "../api/inventory";
import type { ItemInstanceOut } from "../api/types";
import { useAuth } from "../auth/AuthContext";
import { EQUIPMENT_SLOTS } from "../constants/equipmentSlots";

type State =
  | { kind: "loading" }
  | { kind: "loaded"; items: ItemInstanceOut[] }
  | { kind: "error"; message: string };

export function BackpackPage() {
  const { token, hero, refetch } = useAuth();
  const [state, setState] = useState<State>({ kind: "loading" });
  const [pendingId, setPendingId] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

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

  async function handleToggleEquip(item: ItemInstanceOut) {
    if (!token) return;
    setActionError(null);
    setPendingId(item.id);
    try {
      if (item.equipped_slot === null) {
        await equipItem(token, item.id);
      } else {
        await unequipItem(token, item.id);
      }
      await Promise.all([load(), refetch()]);
    } catch (err) {
      setActionError(err instanceof ApiError ? err.message : "Failed to update equipment.");
    } finally {
      setPendingId(null);
    }
  }

  if (!hero) {
    return <p>Loading hero…</p>;
  }

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
          {actionError && <p className="auth-error">{actionError}</p>}
          <p className="backpack-capacity">
            {state.items.length} / {hero.inventory_capacity} items
          </p>
          {state.items.length === 0 ? (
            <p>Your backpack is empty.</p>
          ) : (
            EQUIPMENT_SLOTS.map(({ key, label }) => {
              const slotItems = state.items.filter((item) => item.slot === key);
              return (
                <details key={key} className="backpack-panel" open>
                  <summary className="backpack-panel-summary">
                    {label} ({slotItems.length})
                  </summary>
                  {slotItems.length === 0 ? (
                    <p className="backpack-panel-empty">No {label.toLowerCase()} items.</p>
                  ) : (
                    <ul className="equipment-list">
                      {slotItems.map((item) => (
                        <li key={item.id}>
                          <span className="equipment-slot-label">{item.name}</span>
                          <span className="equipment-slot-filled">
                            <span className="equipment-slot-value">
                              {item.rarity}
                              {item.equipped_slot !== null ? " · equipped" : ""}
                            </span>
                            <button
                              type="button"
                              className="small-button"
                              disabled={pendingId === item.id}
                              onClick={() => handleToggleEquip(item)}
                            >
                              {item.equipped_slot === null ? "Equip" : "Unequip"}
                            </button>
                          </span>
                        </li>
                      ))}
                    </ul>
                  )}
                </details>
              );
            })
          )}
        </>
      )}
    </div>
  );
}
