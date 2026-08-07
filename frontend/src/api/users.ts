import { apiFetch } from "./client";
import type { UserMeResponse } from "./types";

export function getMe(token: string): Promise<UserMeResponse> {
  return apiFetch<UserMeResponse>("/api/v1/users/me", { token });
}
