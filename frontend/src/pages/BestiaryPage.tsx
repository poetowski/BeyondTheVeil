import { useCallback, useEffect, useState } from "react";
import { getBestiary } from "../api/bestiary";
import { ApiError } from "../api/client";
import type { MonsterTemplateOut } from "../api/types";
import { useAuth } from "../auth/AuthContext";

type State =
  | { kind: "loading" }
  | { kind: "loaded"; monsters: MonsterTemplateOut[] }
  | { kind: "error"; message: string };

function levelRangeLabel(monster: MonsterTemplateOut): string {
  return monster.level_range_min === monster.level_range_max
    ? `Level ${monster.level_range_min}`
    : `Level ${monster.level_range_min}–${monster.level_range_max}`;
}

export function BestiaryPage() {
  const { token } = useAuth();
  const [state, setState] = useState<State>({ kind: "loading" });

  const load = useCallback(async () => {
    if (!token) return;
    setState({ kind: "loading" });
    try {
      const monsters = await getBestiary(token);
      setState({ kind: "loaded", monsters });
    } catch (err) {
      setState({
        kind: "error",
        message: err instanceof ApiError ? err.message : "Failed to load the bestiary.",
      });
    }
  }, [token]);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <div className="page">
      <h1>Bestiary</h1>
      {state.kind === "loading" && <p>Consulting old field notes…</p>}
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
          {state.monsters.length === 0 ? (
            <p>Nothing has been catalogued yet.</p>
          ) : (
            <ul className="bestiary-list">
              {state.monsters.map((monster) => (
                <li key={monster.id} className="bestiary-entry">
                  <div className="bestiary-entry-header">
                    <span className="bestiary-entry-name">{monster.name}</span>
                    <span className="bestiary-entry-level">{levelRangeLabel(monster)}</span>
                  </div>
                  {monster.flavor_text && (
                    <p className="bestiary-entry-flavor">{monster.flavor_text}</p>
                  )}
                </li>
              ))}
            </ul>
          )}
        </>
      )}
    </div>
  );
}
