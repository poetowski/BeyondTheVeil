import { useCallback, useEffect, useState } from "react";
import { ApiError } from "../api/client";
import { getLeaderboard } from "../api/leaderboard";
import type { LeaderboardEntryOut } from "../api/types";
import { useAuth } from "../auth/AuthContext";

type State =
  | { kind: "loading" }
  | { kind: "loaded"; entries: LeaderboardEntryOut[] }
  | { kind: "error"; message: string };

export function LeaderboardPage() {
  const { token } = useAuth();
  const [state, setState] = useState<State>({ kind: "loading" });

  const load = useCallback(async () => {
    if (!token) return;
    setState({ kind: "loading" });
    try {
      const entries = await getLeaderboard(token);
      setState({ kind: "loaded", entries });
    } catch (err) {
      setState({
        kind: "error",
        message: err instanceof ApiError ? err.message : "Failed to load the leaderboard.",
      });
    }
  }, [token]);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <div className="page">
      <h1>Leaderboard</h1>
      {state.kind === "loading" && <p>Tallying the standings…</p>}
      {state.kind === "error" && (
        <>
          <p className="auth-error">{state.message}</p>
          <button type="button" onClick={load}>
            Retry
          </button>
        </>
      )}
      {state.kind === "loaded" && (
        <>
          {state.entries.length === 0 ? (
            <p>No heroes have set foot in the veil yet.</p>
          ) : (
            <table className="stat-table">
              <thead>
                <tr>
                  <th>Rank</th>
                  <th>Name</th>
                  <th>Level</th>
                </tr>
              </thead>
              <tbody>
                {state.entries.map((entry) => (
                  <tr key={entry.rank}>
                    <td>#{entry.rank}</td>
                    <td>{entry.name}</td>
                    <td>{entry.level}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </>
      )}
    </div>
  );
}
