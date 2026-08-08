import { apiFetch } from "./client";
import type { ItemInstanceOut } from "./types";

export function getInventory(token: string): Promise<ItemInstanceOut[]> {
  return apiFetch<ItemInstanceOut[]>("/api/v1/inventory", { token });
}
