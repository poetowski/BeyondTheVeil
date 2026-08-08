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
  strength: number;
  dexterity: number;
  vitality: number;
  agility: number;
  intelligence: number;
  spirit: number;
  max_hp: number;
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
  log: Record<string, unknown>[];
  loot: Record<string, unknown>[];
  xp_awarded: number;
}

export interface VeilRunOut {
  id: string;
  status: "in_progress" | "completed";
  started_at: string;
  resolves_at: string;
  result: VeilRunResultOut | null;
}
