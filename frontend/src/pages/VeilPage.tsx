import { useCallback, useEffect, useRef, useState } from "react";
import { ApiError } from "../api/client";
import type { VeilRunOut } from "../api/types";
import { claimRun, enterVeil, getActiveRun } from "../api/veil";
import { useAuth } from "../auth/AuthContext";

type State =
  | { kind: "loading" }
  | { kind: "idle" }
  | { kind: "waiting"; run: VeilRunOut }
  | { kind: "resolving"; run: VeilRunOut }
  | { kind: "resolved"; run: VeilRunOut }
  | { kind: "error"; message: string };

const MAX_CLAIM_RETRIES = 3;
const RETRY_DELAY_MS = 1000;

function msRemaining(run: VeilRunOut): number {
  return new Date(run.resolves_at).getTime() - Date.now();
}

function nextState(run: VeilRunOut): State {
  if (run.result !== null) return { kind: "resolved", run };
  if (msRemaining(run) <= 0) return { kind: "resolving", run };
  return { kind: "waiting", run };
}

function formatCountdown(totalSeconds: number): string {
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes}:${seconds.toString().padStart(2, "0")}`;
}

function errorMessage(err: unknown, fallback: string): string {
  return err instanceof ApiError ? err.message : fallback;
}

function lootItemName(entry: Record<string, unknown>): string {
  return typeof entry.item_name === "string" ? entry.item_name : "an item";
}

function lootItemSlug(entry: Record<string, unknown>): unknown {
  return entry.item_template_slug;
}

export function VeilPage() {
  const { token, refetch } = useAuth();
  const [state, setState] = useState<State>({ kind: "loading" });
  const [tick, setTick] = useState(0);
  const resolvedRef = useRef(false);

  const loadActive = useCallback(async () => {
    if (!token) return;
    setState({ kind: "loading" });
    try {
      const run = await getActiveRun(token);
      setState(run === null ? { kind: "idle" } : nextState(run));
    } catch (err) {
      setState({ kind: "error", message: errorMessage(err, "Failed to load the veil.") });
    }
  }, [token]);

  useEffect(() => {
    loadActive();
  }, [loadActive]);

  // Ticks the countdown display; background tabs throttle setInterval, so
  // also re-check on tab focus rather than relying on the timer alone.
  useEffect(() => {
    const interval = setInterval(() => setTick((t) => t + 1), 1000);
    function onVisible() {
      if (document.visibilityState === "visible") setTick((t) => t + 1);
    }
    document.addEventListener("visibilitychange", onVisible);
    return () => {
      clearInterval(interval);
      document.removeEventListener("visibilitychange", onVisible);
    };
  }, []);

  useEffect(() => {
    if (state.kind === "waiting" && msRemaining(state.run) <= 0) {
      setState({ kind: "resolving", run: state.run });
    }
  }, [state, tick]);

  const attemptClaim = useCallback(
    async (run: VeilRunOut): Promise<VeilRunOut | null> => {
      if (!token) return null;
      try {
        const claimed = await claimRun(token, run.id);
        if (claimed.result !== null) {
          if (!resolvedRef.current) {
            resolvedRef.current = true;
            refetch();
          }
          setState({ kind: "resolved", run: claimed });
        }
        return claimed;
      } catch (err) {
        setState({ kind: "error", message: errorMessage(err, "Failed to claim the reward.") });
        return null;
      }
    },
    [token, refetch],
  );

  const resolvingRunId = state.kind === "resolving" ? state.run.id : null;

  useEffect(() => {
    if (resolvingRunId === null || state.kind !== "resolving") return;
    let cancelled = false;
    const run = state.run;

    (async () => {
      for (let attempt = 0; attempt < MAX_CLAIM_RETRIES; attempt++) {
        const claimed = await attemptClaim(run);
        if (cancelled || claimed === null) return;
        if (claimed.result !== null) return;
        await new Promise((resolve) => setTimeout(resolve, RETRY_DELAY_MS));
      }
      if (!cancelled) {
        setState({ kind: "error", message: "The veil hasn't released its verdict yet. Try again." });
      }
    })();

    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [resolvingRunId]);

  async function handleEnter() {
    if (!token) return;
    resolvedRef.current = false;
    setState({ kind: "loading" });
    try {
      const run = await enterVeil(token);
      setState(nextState(run));
    } catch (err) {
      setState({ kind: "error", message: errorMessage(err, "Failed to enter the veil.") });
    }
  }

  function handleManualClaim() {
    if (state.kind === "resolving") attemptClaim(state.run);
  }

  return (
    <div className="page">
      <h1>The Veil</h1>
      <VeilBody state={state} onEnter={handleEnter} onManualClaim={handleManualClaim} onRetry={loadActive} />
    </div>
  );
}

function VeilBody({
  state,
  onEnter,
  onManualClaim,
  onRetry,
}: {
  state: State;
  onEnter: () => void;
  onManualClaim: () => void;
  onRetry: () => void;
}) {
  switch (state.kind) {
    case "loading":
      return <p>Consulting the veil…</p>;

    case "idle":
      return (
        <>
          <p>The veil is still. Step through when you're ready.</p>
          <button type="button" onClick={onEnter}>
            Enter the Veil
          </button>
        </>
      );

    case "waiting": {
      const seconds = Math.max(0, Math.ceil(msRemaining(state.run) / 1000));
      return (
        <>
          <p>Your hero is inside the veil…</p>
          <p className="veil-countdown">{formatCountdown(seconds)}</p>
        </>
      );
    }

    case "resolving":
      return (
        <>
          <p>The veil is settling…</p>
          <button type="button" onClick={onManualClaim}>
            Claim Reward
          </button>
        </>
      );

    case "resolved": {
      const result = state.run.result!;
      const monsterLabel = result.monster_name ?? "something in the veil";
      const skippedSlugs = new Set(result.loot_skipped.map(lootItemSlug));
      const keptLoot = result.loot.filter((entry) => !skippedSlugs.has(lootItemSlug(entry)));
      return (
        <>
          <p className={result.victory ? "veil-victory" : "veil-defeat"}>
            {result.victory ? "Victory" : "Defeat"} against {monsterLabel}. You gained {result.xp_awarded} XP
            {result.gold_awarded > 0 ? ` and ${result.gold_awarded} gold` : ""}.
          </p>
          <p className="veil-loot-note">
            {keptLoot.length === 0
              ? "No loot this time."
              : `You found: ${keptLoot.map(lootItemName).join(", ")}.`}
          </p>
          {result.loot_skipped.length > 0 && (
            <p className="veil-loot-note">
              Your backpack was full — you left behind: {result.loot_skipped.map(lootItemName).join(", ")}.
            </p>
          )}
          <button type="button" onClick={onEnter}>
            Enter the Veil Again
          </button>
        </>
      );
    }

    case "error":
      return (
        <>
          <p className="auth-error">{state.message}</p>
          <button type="button" onClick={onRetry}>
            Retry
          </button>
        </>
      );
  }
}
