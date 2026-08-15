import { apiFetch } from "./client";
import type { ShopBuyResultOut, ShopOut } from "./types";

export function getShop(token: string): Promise<ShopOut> {
  return apiFetch<ShopOut>("/api/v1/shop", { token });
}

export function buyShopSlot(token: string, slotIndex: number): Promise<ShopBuyResultOut> {
  return apiFetch<ShopBuyResultOut>(`/api/v1/shop/buy/${slotIndex}`, { method: "POST", token });
}
