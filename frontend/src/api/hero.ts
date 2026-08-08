import { apiFetch } from "./client";
import type { HeroOut, StatName } from "./types";

export function allocateStat(token: string, stat: StatName, amount: number): Promise<HeroOut> {
  return apiFetch<HeroOut>("/api/v1/hero/allocate-stat", {
    method: "POST",
    token,
    body: { stat, amount },
  });
}
