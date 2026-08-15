import { apiFetch } from "./client";
import type { MaterialInstanceOut, SellResultOut } from "./types";

export function getMaterials(token: string): Promise<MaterialInstanceOut[]> {
  return apiFetch<MaterialInstanceOut[]>("/api/v1/materials", { token });
}

export function sellMaterial(token: string, materialId: string): Promise<SellResultOut> {
  return apiFetch<SellResultOut>(`/api/v1/materials/${materialId}/sell`, { method: "POST", token });
}
