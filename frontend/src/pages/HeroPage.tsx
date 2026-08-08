import { useState } from "react";
import { allocateStat } from "../api/hero";
import { ApiError } from "../api/client";
import type { HeroOut, StatName } from "../api/types";
import { useAuth } from "../auth/AuthContext";

const EQUIPMENT_SLOTS = ["Weapon", "Helmet", "Shield", "Armor", "Amulet", "Spell Skill"];

const STAT_ROWS: {
  label: string;
  stat: StatName;
  totalKey: keyof HeroOut;
  baseKey: keyof HeroOut;
  bonusKey: keyof HeroOut;
}[] = [
  { label: "Strength", stat: "strength", totalKey: "strength", baseKey: "base_strength", bonusKey: "bonus_strength" },
  { label: "Dexterity", stat: "dexterity", totalKey: "dexterity", baseKey: "base_dexterity", bonusKey: "bonus_dexterity" },
  { label: "Intelligence", stat: "intelligence", totalKey: "intelligence", baseKey: "base_intelligence", bonusKey: "bonus_intelligence" },
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
  const [allocating, setAllocating] = useState<StatName | null>(null);
  const [allocateError, setAllocateError] = useState<string | null>(null);

  if (!hero) {
    return <p>Loading hero…</p>;
  }

  async function handleAllocate(stat: StatName) {
    if (!token) return;
    setAllocateError(null);
    setAllocating(stat);
    try {
      await allocateStat(token, stat, 1);
      await refetch();
    } catch (err) {
      setAllocateError(err instanceof ApiError ? err.message : "Failed to allocate stat point.");
    } finally {
      setAllocating(null);
    }
  }

  return (
    <div className="page hero-page">
      <h1>{hero.name}</h1>
      <p className="hero-meta">
        Level {hero.level} · {hero.xp_into_level}/{hero.xp_for_next_level} XP · {hero.max_hp} max
        HP · {hero.gold} gold
      </p>

      <h2>Stats</h2>
      {hero.available_stat_points > 0 && (
        <p>
          <span className="stat-points-badge">{hero.available_stat_points} points available</span>
        </p>
      )}
      {allocateError && <p className="auth-error">{allocateError}</p>}
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
                  {hero.available_stat_points > 0 && (
                    <button
                      type="button"
                      className="stat-allocate-button"
                      disabled={allocating !== null}
                      onClick={() => handleAllocate(row.stat)}
                    >
                      {allocating === row.stat ? "…" : "+1"}
                    </button>
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>

      <h2>Equipment</h2>
      <ul className="equipment-list">
        {EQUIPMENT_SLOTS.map((slot) => (
          <li key={slot}>
            <span className="equipment-slot-label">{slot}</span>
            <span className="equipment-slot-value">— empty —</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
