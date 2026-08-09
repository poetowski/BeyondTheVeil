import type { ItemInstanceOut } from "../api/types";

const STAT_LABELS: Record<string, string> = {
  strength: "Strength",
  dexterity: "Dexterity",
  intelligence: "Intelligence",
  vitality: "Vitality",
  agility: "Agility",
  spirit: "Spirit",
};

/** Compact summary of an item's mechanical effects, e.g. "Damage 2-6",
 * "Defense 3 · +2 Vitality". Empty string if the item does nothing. */
export function formatItemStats(item: ItemInstanceOut): string {
  const parts: string[] = [];

  if (item.damage_min !== null && item.damage_max !== null) {
    parts.push(`Damage ${item.damage_min}-${item.damage_max}`);
  }
  if (item.defense > 0) {
    parts.push(`Defense ${item.defense}`);
  }
  if (item.bonus_max_hp > 0) {
    parts.push(`+${item.bonus_max_hp} Max HP`);
  }
  for (const [stat, bonus] of Object.entries(item.base_stats)) {
    parts.push(`+${bonus} ${STAT_LABELS[stat] ?? stat}`);
  }

  return parts.join(" · ");
}
