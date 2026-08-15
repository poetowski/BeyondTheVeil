import { useCallback, useEffect, useState } from "react";
import { getConsumables, useConsumable as consumeConsumable } from "../api/alchemy";
import { ApiError } from "../api/client";
import { applyRune, equipItem, getInventory, unequipItem } from "../api/inventory";
import { getRunes } from "../api/runes";
import type { ConsumableInstanceOut, ItemInstanceOut, RuneInstanceOut } from "../api/types";
import { useAuth } from "../auth/AuthContext";
import { ItemIcon } from "../components/ItemIcon";
import { RuneIcon } from "../components/RuneIcon";
import { EQUIPMENT_SLOTS } from "../constants/equipmentSlots";
import { formatItemStats } from "../utils/formatItemStats";

type State =
  | { kind: "loading" }
  | {
      kind: "loaded";
      items: ItemInstanceOut[];
      consumables: ConsumableInstanceOut[];
      runes: RuneInstanceOut[];
    }
  | { kind: "error"; message: string };

function ConsumableIcon({ slug, name }: { slug: string; name: string }) {
  const [missing, setMissing] = useState(false);
  if (missing) {
    return <div className="item-icon item-icon--missing" aria-hidden="true" />;
  }
  return (
    <img
      className="item-icon"
      src={`/consumables/${slug}.svg`}
      alt={name}
      onError={() => setMissing(true)}
    />
  );
}

export function BackpackPage() {
  const { token, hero, refetch } = useAuth();
  const [state, setState] = useState<State>({ kind: "loading" });
  const [pendingId, setPendingId] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [selectedRuneByItem, setSelectedRuneByItem] = useState<Record<string, string>>({});

  const load = useCallback(async () => {
    if (!token) return;
    setState({ kind: "loading" });
    try {
      const [items, consumables, runes] = await Promise.all([
        getInventory(token),
        getConsumables(token),
        getRunes(token),
      ]);
      setState({ kind: "loaded", items, consumables, runes });
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

  async function handleApplyRune(itemId: string, runeInstanceId: string) {
    if (!token || !runeInstanceId) return;
    setActionError(null);
    setPendingId(itemId);
    try {
      await applyRune(token, itemId, runeInstanceId);
      await Promise.all([load(), refetch()]);
    } catch (err) {
      setActionError(err instanceof ApiError ? err.message : "Failed to apply that rune.");
    } finally {
      setPendingId(null);
    }
  }

  async function handleUseConsumable(consumableId: string) {
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

  if (!hero) {
    return <p>Loading hero…</p>;
  }

  const consumableCount =
    state.kind === "loaded" ? state.consumables.reduce((sum, c) => sum + c.quantity, 0) : 0;
  const runeCount = state.kind === "loaded" ? state.runes.reduce((sum, r) => sum + r.quantity, 0) : 0;
  const itemCount = state.kind === "loaded" ? state.items.length : 0;
  const usedCapacity = itemCount + consumableCount + runeCount;

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
            {usedCapacity} / {hero.inventory_capacity} items
          </p>

          <details className="backpack-panel" open>
            <summary className="backpack-panel-summary">Consumables ({consumableCount})</summary>
            {state.consumables.length === 0 ? (
              <p className="backpack-panel-empty">No consumables.</p>
            ) : (
              <ul className="equipment-list">
                {state.consumables.map((consumable) => (
                  <li key={consumable.id} className="list-row">
                    <span className="equipment-slot-label">{consumable.name}</span>
                    <ConsumableIcon slug={consumable.slug} name={consumable.name} />
                    <span className="equipment-slot-filled">
                      <span className="equipment-slot-value">×{consumable.quantity}</span>
                      <button
                        type="button"
                        className="small-button"
                        disabled={pendingId === consumable.id}
                        onClick={() => handleUseConsumable(consumable.id)}
                      >
                        Use
                      </button>
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </details>

          <details className="backpack-panel" open>
            <summary className="backpack-panel-summary">Runes ({runeCount})</summary>
            {state.runes.length === 0 ? (
              <p className="backpack-panel-empty">No runes.</p>
            ) : (
              <ul className="equipment-list">
                {state.runes.map((rune) => (
                  <li key={rune.id} className="list-row">
                    <span className="equipment-slot-label">{rune.name}</span>
                    <RuneIcon slug={rune.slug} name={rune.name} />
                    <span className="equipment-slot-filled">
                      <span className="equipment-slot-value">×{rune.quantity}</span>
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </details>

          {EQUIPMENT_SLOTS.map(({ key, label }) => {
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
                    {slotItems.map((item) => {
                      const stats = formatItemStats(item);
                      return (
                        <li key={item.id} className="list-row">
                          <span className="equipment-slot-label">{item.name}</span>
                          <ItemIcon slug={item.slug} name={item.name} />
                          <span className="equipment-slot-filled">
                            <span className="equipment-slot-value">
                              {item.rarity}
                              {stats ? ` · ${stats}` : ""}
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
                            {item.rune_name !== null ? (
                              <span className="equipment-slot-value">Runed: {item.rune_name}</span>
                            ) : state.runes.length > 0 ? (
                              <>
                                <select
                                  value={selectedRuneByItem[item.id] ?? state.runes[0].id}
                                  onChange={(e) =>
                                    setSelectedRuneByItem((prev) => ({
                                      ...prev,
                                      [item.id]: e.target.value,
                                    }))
                                  }
                                >
                                  {state.runes.map((rune) => (
                                    <option key={rune.id} value={rune.id}>
                                      {rune.name}
                                    </option>
                                  ))}
                                </select>
                                <button
                                  type="button"
                                  className="small-button"
                                  disabled={pendingId === item.id}
                                  onClick={() =>
                                    handleApplyRune(
                                      item.id,
                                      selectedRuneByItem[item.id] ?? state.runes[0].id,
                                    )
                                  }
                                >
                                  Apply Rune
                                </button>
                              </>
                            ) : null}
                          </span>
                        </li>
                      );
                    })}
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
