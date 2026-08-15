import { apiFetch } from "./client";
import type { RuneInstanceOut } from "./types";

export function getRunes(token: string): Promise<RuneInstanceOut[]> {
  return apiFetch<RuneInstanceOut[]>("/api/v1/runes", { token });
}
