import { apiFetch } from "./client";
import type { AvatarTemplateOut, HeroOut } from "./types";

export function getAvatars(token: string): Promise<AvatarTemplateOut[]> {
  return apiFetch<AvatarTemplateOut[]>("/api/v1/avatars", { token });
}

export function unlockAvatar(token: string, avatarSlug: string): Promise<HeroOut> {
  return apiFetch<HeroOut>(`/api/v1/avatars/${avatarSlug}/unlock`, { method: "POST", token });
}
