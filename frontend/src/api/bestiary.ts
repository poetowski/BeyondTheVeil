import { apiFetch } from "./client";
import type { MonsterTemplateOut } from "./types";

export function getBestiary(token: string): Promise<MonsterTemplateOut[]> {
  return apiFetch<MonsterTemplateOut[]>("/api/v1/bestiary", { token });
}
