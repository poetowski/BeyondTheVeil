import { apiFetch } from "./client";
import type { LeaderboardEntryOut } from "./types";

export function getLeaderboard(token: string): Promise<LeaderboardEntryOut[]> {
  return apiFetch<LeaderboardEntryOut[]>("/api/v1/leaderboard", { token });
}
