import { apiFetch } from "./client";
import type { VeilRunOut } from "./types";

export function enterVeil(token: string): Promise<VeilRunOut> {
  return apiFetch<VeilRunOut>("/api/v1/veil/enter", { method: "POST", token });
}

export function getActiveRun(token: string): Promise<VeilRunOut | null> {
  return apiFetch<VeilRunOut | null>("/api/v1/veil/active", { token });
}

export function claimRun(token: string, runId: string): Promise<VeilRunOut> {
  return apiFetch<VeilRunOut>(`/api/v1/veil/${runId}/claim`, { method: "POST", token });
}
