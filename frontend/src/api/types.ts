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
  weapon_damage_min: number | null;
  weapon_damage_max: number | null;
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
}

export interface VeilRunOut {
  id: string;
  status: "in_progress" | "completed";
  started_at: string;
  resolves_at: string;
  result: VeilRunResultOut | null;
}

export type EquipmentSlot = "weapon" | "helmet" | "shield" | "armor" | "amulet" | "spell_skill";

export type StatName = "strength" | "dexterity" | "intelligence" | "vitality" | "agility" | "spirit";

export type ItemRarity = "common" | "uncommon" | "rare" | "epic" | "legendary";

export interface ItemInstanceOut {
  id: string;
  name: string;
  slot: EquipmentSlot;
  rarity: ItemRarity;
  base_stats: Record<string, number>;
  rolled_stats: Record<string, number> | null;
  equipped_slot: EquipmentSlot | null;
  damage_min: number | null;
  damage_max: number | null;
  defense: number;
  bonus_max_hp: number;
  acquired_at: string;
}

export interface MaterialInstanceOut {
  id: string;
  name: string;
  description: string | null;
  quantity: number;
  category: CraftingCategory;
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

export type CampaignNodeStatus = "locked" | "available" | "cleared";

export interface CampaignNodeOut {
  id: string;
  order_index: number;
  name: string;
  required_level: number;
  gold_cost: number;
  monster_name: string;
  status: CampaignNodeStatus;
}

export interface ConsumableInstanceOut {
  id: string;
  name: string;
  description: string | null;
  quantity: number;
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
  output_consumable_name: string;
  output_quantity: number;
  ingredients: RecipeIngredientOut[];
  craftable: boolean;
}

export interface LeaderboardEntryOut {
  rank: number;
  name: string;
  level: number;
}
