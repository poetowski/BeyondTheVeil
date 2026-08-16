import { apiFetch } from "./client";
import type { HeroOut, StatName } from "./types";

export function trainStat(token: string, stat: StatName): Promise<HeroOut> {
  return apiFetch<HeroOut>("/api/v1/hero/train", { method: "POST", token, body: { stat } });
}

export function setAvatar(token: string, avatarSlug: string): Promise<HeroOut> {
  return apiFetch<HeroOut>("/api/v1/hero/avatar", {
    method: "POST",
    token,
    body: { avatar_slug: avatarSlug },
  });
}
