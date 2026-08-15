import { useCallback, useEffect, useState } from "react";
import { buyShopSlot, getShop } from "../api/shop";
import { ApiError } from "../api/client";
import type { ShopOut, ShopSlotOut } from "../api/types";
import { useAuth } from "../auth/AuthContext";
import { ItemIcon } from "../components/ItemIcon";
import { MaterialIcon } from "../components/MaterialIcon";

type State = { kind: "loading" } | { kind: "loaded"; shop: ShopOut } | { kind: "error"; message: string };

export function ShopPage() {
  const { token, refetch } = useAuth();
  const [state, setState] = useState<State>({ kind: "loading" });
  const [pendingSlot, setPendingSlot] = useState<number | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!token) return;
    setState({ kind: "loading" });
    try {
      const shop = await getShop(token);
      setState({ kind: "loaded", shop });
    } catch (err) {
      setState({
        kind: "error",
        message: err instanceof ApiError ? err.message : "Failed to load the shop.",
      });
    }
  }, [token]);

  useEffect(() => {
    load();
  }, [load]);

  async function handleBuy(slotIndex: number) {
    if (!token) return;
    setActionError(null);
    setPendingSlot(slotIndex);
    try {
      await buyShopSlot(token, slotIndex);
      await Promise.all([load(), refetch()]);
    } catch (err) {
      setActionError(err instanceof ApiError ? err.message : "Failed to buy that.");
    } finally {
      setPendingSlot(null);
    }
  }

  function renderSlot(slot: ShopSlotOut) {
    return (
      <li key={slot.slot_index} className="list-row">
        <span className="equipment-slot-label">{slot.name}</span>
        {slot.slot_type === "item" ? (
          <ItemIcon slug={slot.slug} name={slot.name} />
        ) : (
          <MaterialIcon slug={slot.slug} name={slot.name} />
        )}
        <span className="equipment-slot-filled">
          <span className="equipment-slot-value">{slot.description}</span>
          <button
            type="button"
            className="small-button"
            disabled={slot.already_bought || pendingSlot === slot.slot_index}
            onClick={() => handleBuy(slot.slot_index)}
          >
            {slot.already_bought ? "Sold" : `Buy (${slot.price}g)`}
          </button>
        </span>
      </li>
    );
  }

  return (
    <div className="page">
      <h1>Shop</h1>
      {state.kind === "loading" && <p>Setting out today's wares…</p>}
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

          <details className="backpack-panel" open>
            <summary className="backpack-panel-summary">Gear</summary>
            <ul className="equipment-list">
              {state.shop.slots.filter((s) => s.slot_type === "item").map(renderSlot)}
            </ul>
          </details>

          <details className="backpack-panel" open>
            <summary className="backpack-panel-summary">Materials</summary>
            <ul className="equipment-list">
              {state.shop.slots.filter((s) => s.slot_type === "material").map(renderSlot)}
            </ul>
          </details>

          <p className="backpack-panel-empty">
            Today's stock resets tomorrow. Each slot can be bought once.
          </p>
        </>
      )}
    </div>
  );
}
