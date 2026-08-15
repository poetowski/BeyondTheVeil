export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface UserOut {
  id: string;
  email: string;
}

export interface HeroOut {
  id: string;
  name: string;
  level: number;
  xp: number;
  xp_to_next_level: number;
  gold: number;
  inventory_capacity: number;
  strength: number;
  dexterity: number;
  intelligence: number;
  vitality: number;
  agility: number;
  spirit: number;
  base_strength: number;
  base_dexterity: number;
  base_intelligence: number;
  base_vitality: number;
  base_agility: number;
  base_spirit: number;
  bonus_strength: number;
  bonus_dexterity: number;
  bonus_intelligence: number;
  bonus_vitality: number;
  bonus_agility: number;
  bonus_spirit: number;
  current_hp: number;
  max_hp: number;
  damage_min: number;
  damage_max: number;
  spell_damage_min: number;
  spell_damage_max: number;
  defense_shield: number;
  defense_armor: number;
  defense_helmet: number;
  train_costs: Record<StatName, number>;
}

export interface UserMeResponse {
  user: UserOut;
  hero: HeroOut;
}

export interface SignupRequest {
  email: string;
  password: string;
  hero_name: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface VeilRunResultOut {
  victory: boolean;
  monster_name: string | null;
  log: Record<string, unknown>[];
  loot: Record<string, unknown>[];
  loot_skipped: Record<string, unknown>[];
  material_loot: Record<string, unknown>[];
  xp_awarded: number;
  gold_awarded: number;
  hero_hp_before: number | null;
  hero_hp_after: number | null;
  monster_hp_after: number | null;
}

export interface VeilEncounterOut {
  monster_name: string | null;
  monster_stats: Record<StatName, number> | null;
  monster_max_hp: number | null;
  monster_slug: string | null;
  monster_level: number | null;
  monster_damage_min: number | null;
  monster_damage_max: number | null;
  monster_spell_damage_min: number | null;
  monster_spell_damage_max: number | null;
  monster_defense: number | null;
}

export interface VeilRunOut {
  id: string;
  status: "in_progress" | "completed";
  started_at: string;
  resolves_at: string;
  encounter: VeilEncounterOut | null;
  result: VeilRunResultOut | null;
}

export type EquipmentSlot = "weapon" | "helmet" | "shield" | "armor" | "amulet" | "spell_skill";

export type StatName = "strength" | "dexterity" | "intelligence" | "vitality" | "agility" | "spirit";

export type ItemRarity = "common" | "uncommon" | "rare" | "epic" | "legendary";

export interface ItemInstanceOut {
  id: string;
  slug: string;
  name: string;
  slot: EquipmentSlot;
  rarity: ItemRarity;
  base_stats: Record<string, number>;
  rolled_stats: Record<string, number> | null;
  equipped_slot: EquipmentSlot | null;
  damage_min: number | null;
  damage_max: number | null;
  spell_damage_min: number | null;
  spell_damage_max: number | null;
  defense: number;
  bonus_max_hp: number;
  rune_template_id: string | null;
  rune_slug: string | null;
  rune_name: string | null;
  rune_stat_bonuses: Record<string, number> | null;
  price: number;
  acquired_at: string;
}

export interface RuneInstanceOut {
  id: string;
  slug: string;
  name: string;
  description: string | null;
  stat_bonuses: Record<string, number>;
  quantity: number;
  price: number;
  acquired_at: string;
}

export interface MaterialInstanceOut {
  id: string;
  slug: string;
  name: string;
  description: string | null;
  quantity: number;
  category: CraftingCategory;
  price: number;
  acquired_at: string;
}

export interface MonsterTemplateOut {
  id: string;
  slug: string;
  name: string;
  level_range_min: number;
  level_range_max: number;
  flavor_text: string | null;
}

export interface ConsumableInstanceOut {
  id: string;
  slug: string;
  name: string;
  description: string | null;
  quantity: number;
  price: number;
  acquired_at: string;
}

export type CraftingCategory = "alchemy" | "forge";

export interface RecipeIngredientOut {
  material_name: string;
  material_template_slug: string;
  quantity_required: number;
  quantity_owned: number;
}

export interface CraftingRecipeOut {
  id: string;
  slug: string;
  name: string;
  category: CraftingCategory;
  level_requirement: number;
  output_name: string;
  output_type: "consumable" | "rune";
  output_quantity: number;
  ingredients: RecipeIngredientOut[];
  craftable: boolean;
}

export interface CraftResultOut {
  output_type: "consumable" | "rune";
  consumable: ConsumableInstanceOut | null;
  rune: RuneInstanceOut | null;
}

export interface LeaderboardEntryOut {
  rank: number;
  name: string;
  level: number;
}

export interface ShopSlotOut {
  slot_index: number;
  slot_type: "item" | "material";
  template_id: string;
  slug: string;
  name: string;
  description: string | null;
  price: number;
  already_bought: boolean;
  item_slot: EquipmentSlot | null;
  item_rarity: ItemRarity | null;
  material_category: CraftingCategory | null;
}

export interface ShopOut {
  shop_date: string;
  slots: ShopSlotOut[];
}

export interface ShopBuyResultOut {
  slot_type: "item" | "material";
  item: ItemInstanceOut | null;
  material: MaterialInstanceOut | null;
  gold_spent: number;
}

export interface SellResultOut {
  gold_gained: number;
}
