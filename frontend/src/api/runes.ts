import { apiFetch } from "./client";
import type { RuneInstanceOut, SellResultOut } from "./types";

export function getRunes(token: string): Promise<RuneInstanceOut[]> {
  return apiFetch<RuneInstanceOut[]>("/api/v1/runes", { token });
}

export function sellRune(token: string, runeId: string): Promise<SellResultOut> {
  return apiFetch<SellResultOut>(`/api/v1/runes/${runeId}/sell`, { method: "POST", token });
}
