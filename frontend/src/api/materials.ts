import { apiFetch } from "./client";
import type { MaterialInstanceOut } from "./types";

export function getMaterials(token: string): Promise<MaterialInstanceOut[]> {
  return apiFetch<MaterialInstanceOut[]>("/api/v1/materials", { token });
}
