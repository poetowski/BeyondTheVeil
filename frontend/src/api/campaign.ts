import { apiFetch } from "./client";
import type { CampaignChapterOut, CampaignNodeOut, VeilRunOut } from "./types";

export function getCampaignChapters(token: string): Promise<CampaignChapterOut[]> {
  return apiFetch<CampaignChapterOut[]>("/api/v1/campaign/chapters", { token });
}

export function getCampaignNodes(token: string): Promise<CampaignNodeOut[]> {
  return apiFetch<CampaignNodeOut[]>("/api/v1/campaign/nodes", { token });
}

export function enterCampaignNode(token: string, nodeId: string): Promise<VeilRunOut> {
  return apiFetch<VeilRunOut>(`/api/v1/campaign/nodes/${nodeId}/enter`, {
    method: "POST",
    token,
  });
}
