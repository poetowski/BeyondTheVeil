import { apiFetch } from "./client";
import type { ItemInstanceOut } from "./types";

export function getInventory(token: string): Promise<ItemInstanceOut[]> {
  return apiFetch<ItemInstanceOut[]>("/api/v1/inventory", { token });
}

export function equipItem(token: string, itemId: string): Promise<ItemInstanceOut> {
  return apiFetch<ItemInstanceOut>(`/api/v1/inventory/${itemId}/equip`, { method: "POST", token });
}

export function unequipItem(token: string, itemId: string): Promise<ItemInstanceOut> {
  return apiFetch<ItemInstanceOut>(`/api/v1/inventory/${itemId}/unequip`, { method: "POST", token });
}
