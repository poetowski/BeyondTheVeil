import { apiFetch } from "./client";
import type { CampaignNodeOut, VeilRunOut } from "./types";

export function getCampaignNodes(token: string): Promise<CampaignNodeOut[]> {
  return apiFetch<CampaignNodeOut[]>("/api/v1/campaign/nodes", { token });
}

export function enterCampaignNode(token: string, nodeId: string): Promise<VeilRunOut> {
  return apiFetch<VeilRunOut>(`/api/v1/campaign/nodes/${nodeId}/enter`, {
    method: "POST",
    token,
  });
}
