import { apiFetch } from "./client";
import type { HeroOut, StatName } from "./types";

export function trainStat(token: string, stat: StatName): Promise<HeroOut> {
  return apiFetch<HeroOut>("/api/v1/hero/train", { method: "POST", token, body: { stat } });
}
