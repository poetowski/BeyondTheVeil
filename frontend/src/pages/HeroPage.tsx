import { useAuth } from "../auth/AuthContext";
import type { HeroOut } from "../api/types";

const EQUIPMENT_SLOTS = ["Weapon", "Helmet", "Shield", "Armor", "Amulet", "Spell Skill"];

const STAT_ROWS: { label: string; totalKey: keyof HeroOut; baseKey: keyof HeroOut; bonusKey: keyof HeroOut }[] = [
  { label: "Strength", totalKey: "strength", baseKey: "base_strength", bonusKey: "bonus_strength" },
  { label: "Dexterity", totalKey: "dexterity", baseKey: "base_dexterity", bonusKey: "bonus_dexterity" },
  { label: "Intelligence", totalKey: "intelligence", baseKey: "base_intelligence", bonusKey: "bonus_intelligence" },
  { label: "Vitality", totalKey: "vitality", baseKey: "base_vitality", bonusKey: "bonus_vitality" },
  { label: "Agility", totalKey: "agility", baseKey: "base_agility", bonusKey: "bonus_agility" },
  { label: "Spirit", totalKey: "spirit", baseKey: "base_spirit", bonusKey: "bonus_spirit" },
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
  const { hero } = useAuth();

  if (!hero) {
    return <p>Loading hero…</p>;
  }

  return (
    <div className="page hero-page">
      <h1>{hero.name}</h1>
      <p className="hero-meta">
        Level {hero.level} · {hero.xp} XP · {hero.max_hp} max HP
      </p>

      <h2>Stats</h2>
      <table className="stat-table">
        <thead>
          <tr>
            <th>Stat</th>
            <th>Base</th>
            <th>Bonus</th>
            <th>Total</th>
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
