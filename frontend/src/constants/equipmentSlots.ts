import type { EquipmentSlot } from "../api/types";

export const EQUIPMENT_SLOTS: { key: EquipmentSlot; label: string }[] = [
  { key: "weapon", label: "Weapon" },
  { key: "helmet", label: "Helmet" },
  { key: "shield", label: "Shield" },
  { key: "armor", label: "Armor" },
  { key: "amulet", label: "Amulet" },
  { key: "spell_skill", label: "Spell Skill" },
];
