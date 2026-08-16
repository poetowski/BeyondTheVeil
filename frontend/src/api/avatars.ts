import { apiFetch } from "./client";
import type { AvatarTemplateOut } from "./types";

export function getAvatars(token: string): Promise<AvatarTemplateOut[]> {
  return apiFetch<AvatarTemplateOut[]>("/api/v1/avatars", { token });
}
