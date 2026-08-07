import { useAuth } from "../auth/AuthContext";

const EQUIPMENT_SLOTS = ["Weapon", "Helmet", "Shield", "Armor", "Amulet", "Spell Skill"];

const STAT_ROWS: { label: string; key: "strength" | "dexterity" | "vitality" | "agility" | "intelligence" | "spirit" }[] = [
  { label: "Strength", key: "strength" },
  { label: "Dexterity", key: "dexterity" },
  { label: "Vitality", key: "vitality" },
  { label: "Agility", key: "agility" },
  { label: "Intelligence", key: "intelligence" },
  { label: "Spirit", key: "spirit" },
];

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
        <tbody>
          {STAT_ROWS.map((row) => (
            <tr key={row.key}>
              <td>{row.label}</td>
              <td>{hero[row.key]}</td>
            </tr>
          ))}
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
