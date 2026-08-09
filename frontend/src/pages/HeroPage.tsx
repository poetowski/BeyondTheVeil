import { useCallback, useEffect, useState } from "react";
import { ApiError } from "../api/client";
import { trainStat } from "../api/hero";
import { getInventory, unequipItem } from "../api/inventory";
import type { EquipmentSlot, HeroOut, ItemInstanceOut, StatName } from "../api/types";
import { useAuth } from "../auth/AuthContext";

const EQUIPMENT_SLOTS: { key: EquipmentSlot; label: string }[] = [
  { key: "weapon", label: "Weapon" },
  { key: "helmet", label: "Helmet" },
  { key: "shield", label: "Shield" },
  { key: "armor", label: "Armor" },
  { key: "amulet", label: "Amulet" },
  { key: "spell_skill", label: "Spell Skill" },
];

const STAT_ROWS: {
  label: string;
  stat: StatName;
  totalKey: keyof HeroOut;
  baseKey: keyof HeroOut;
  bonusKey: keyof HeroOut;
}[] = [
  { label: "Strength", stat: "strength", totalKey: "strength", baseKey: "base_strength", bonusKey: "bonus_strength" },
  { label: "Dexterity", stat: "dexterity", totalKey: "dexterity", baseKey: "base_dexterity", bonusKey: "bonus_dexterity" },
  {
    label: "Intelligence",
    stat: "intelligence",
    totalKey: "intelligence",
    baseKey: "base_intelligence",
    bonusKey: "bonus_intelligence",
  },
  { label: "Vitality", stat: "vitality", totalKey: "vitality", baseKey: "base_vitality", bonusKey: "bonus_vitality" },
  { label: "Agility", stat: "agility", totalKey: "agility", baseKey: "base_agility", bonusKey: "bonus_agility" },
  { label: "Spirit", stat: "spirit", totalKey: "spirit", baseKey: "base_spirit", bonusKey: "bonus_spirit" },
];

function formatSigned(n: number): string {
  if (n > 0) return `+${n}`;
  if (n < 0) return `${n}`;
  return "+0";
}

function bonusClass(n: number): string {
  if (n > 0) return "stat-bonus-positive";
  if (n < 0) return "stat-bonus-negative";
  return "stat-bonus-zero";
}

export function HeroPage() {
  const { hero, token, refetch } = useAuth();
  const [items, setItems] = useState<ItemInstanceOut[]>([]);
  const [pendingAction, setPendingAction] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  const loadInventory = useCallback(async () => {
    if (!token) return;
    try {
      setItems(await getInventory(token));
    } catch {
      // Backpack page is the source of truth for load failures; equipment
      // section just stays empty here.
    }
  }, [token]);

  useEffect(() => {
    loadInventory();
  }, [loadInventory]);

  async function handleUnequip(itemId: string) {
    if (!token) return;
    setActionError(null);
    setPendingAction(itemId);
    try {
      await unequipItem(token, itemId);
      await Promise.all([loadInventory(), refetch()]);
    } catch (err) {
      setActionError(err instanceof ApiError ? err.message : "Failed to unequip that item.");
    } finally {
      setPendingAction(null);
    }
  }

  async function handleTrain(stat: StatName) {
    if (!token) return;
    setActionError(null);
    setPendingAction(stat);
    try {
      await trainStat(token, stat);
      await refetch();
    } catch (err) {
      setActionError(err instanceof ApiError ? err.message : "Failed to train that stat.");
    } finally {
      setPendingAction(null);
    }
  }

  if (!hero) {
    return <p>Loading hero…</p>;
  }

  const equippedBySlot = new Map(
    items.filter((item) => item.equipped_slot !== null).map((item) => [item.equipped_slot, item]),
  );

  return (
    <div className="page hero-page">
      <h1>{hero.name}</h1>
      <p className="hero-meta">
        Level {hero.level} · {hero.xp}/{hero.xp_to_next_level} XP · {hero.max_hp} max HP · {hero.gold} gold
      </p>
      {actionError && <p className="auth-error">{actionError}</p>}

      <h2>Stats</h2>
      <table className="stat-table">
        <thead>
          <tr>
            <th>Stat</th>
            <th>Base</th>
            <th>Bonus</th>
            <th>Total</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {STAT_ROWS.map((row) => {
            const bonus = hero[row.bonusKey] as number;
            return (
              <tr key={row.label}>
                <td>{row.label}</td>
                <td>{hero[row.baseKey] as number}</td>
                <td className={bonusClass(bonus)}>{formatSigned(bonus)}</td>
                <td>{hero[row.totalKey] as number}</td>
                <td>
                  <button
                    type="button"
                    className="small-button"
                    disabled={pendingAction === row.stat}
                    onClick={() => handleTrain(row.stat)}
                  >
                    Train +1
                  </button>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>

      <h2>Equipment</h2>
      <ul className="equipment-list">
        {EQUIPMENT_SLOTS.map(({ key, label }) => {
          const item = equippedBySlot.get(key);
          return (
            <li key={key}>
              <span className="equipment-slot-label">{label}</span>
              {item ? (
                <span className="equipment-slot-filled">
                  {item.name}
                  <button
                    type="button"
                    className="small-button"
                    disabled={pendingAction === item.id}
                    onClick={() => handleUnequip(item.id)}
                  >
                    Unequip
                  </button>
                </span>
              ) : (
                <span className="equipment-slot-value">— empty —</span>
              )}
            </li>
          );
        })}
      </ul>
    </div>
  );
}
