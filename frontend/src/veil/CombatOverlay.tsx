import { useCallback, useEffect, useRef, useState } from "react";
import { ApiError } from "../api/client";
import type { StatName, VeilRunOut } from "../api/types";
import { claimRun } from "../api/veil";
import { useAuth } from "../auth/AuthContext";
import { ProgressBar } from "../components/ProgressBar";
import "./CombatOverlay.css";

const MAX_CLAIM_RETRIES = 3;
const RETRY_DELAY_MS = 1000;

const STAT_ORDER: { key: StatName; label: string }[] = [
  { key: "strength", label: "Strength" },
  { key: "dexterity", label: "Dexterity" },
  { key: "intelligence", label: "Intelligence" },
  { key: "vitality", label: "Vitality" },
  { key: "agility", label: "Agility" },
  { key: "spirit", label: "Spirit" },
];

type Phase = "waiting" | "resolving" | "resolved" | "error";

function msRemaining(run: VeilRunOut): number {
  return new Date(run.resolves_at).getTime() - Date.now();
}

function nextPhase(run: VeilRunOut): Phase {
  if (run.result !== null) return "resolved";
  return msRemaining(run) <= 0 ? "resolving" : "waiting";
}

function formatCountdown(totalSeconds: number): string {
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes}:${seconds.toString().padStart(2, "0")}`;
}

function errorMessage(err: unknown, fallback: string): string {
  return err instanceof ApiError ? err.message : fallback;
}

function formatRange(min: number, max: number): string {
  return min === max ? `${min}` : `${min}-${max}`;
}

function formatLevelRange(min: number | null, max: number | null): string {
  if (min === null || max === null) return "—";
  return min === max ? `Level ${min}` : `Level ${min}–${max}`;
}

function CombatPanelArt({ src, alt }: { src: string; alt: string }) {
  const [missing, setMissing] = useState(false);
  if (missing) {
    return <div className="combat-panel-art combat-panel-art--missing" aria-hidden="true" />;
  }
  return (
    <img className="combat-panel-art" src={src} alt={alt} onError={() => setMissing(true)} />
  );
}

function lootItemName(entry: Record<string, unknown>): string {
  return typeof entry.item_name === "string" ? entry.item_name : "an item";
}

function lootItemSlug(entry: Record<string, unknown>): unknown {
  return entry.item_template_slug;
}

function materialLootName(entry: Record<string, unknown>): string {
  return typeof entry.material_name === "string" ? entry.material_name : "a material";
}

interface CombatOverlayProps {
  run: VeilRunOut;
  onExit: () => void;
}

export function CombatOverlay({ run: incomingRun, onExit }: CombatOverlayProps) {
  const { token, hero, refetch } = useAuth();
  const [run, setRun] = useState(incomingRun);
  const [phase, setPhase] = useState<Phase>(() => nextPhase(incomingRun));
  const [message, setMessage] = useState<string | null>(null);
  const [tick, setTick] = useState(0);
  const resolvedRef = useRef(incomingRun.result !== null);

  // A different run arriving (a fresh "Enter the Veil" after the previous
  // one was exited) resets local state to match it.
  useEffect(() => {
    setRun(incomingRun);
    setPhase(nextPhase(incomingRun));
    resolvedRef.current = incomingRun.result !== null;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [incomingRun.id]);

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
    if (phase === "waiting" && msRemaining(run) <= 0) {
      setPhase("resolving");
    }
  }, [phase, run, tick]);

  const attemptClaim = useCallback(
    async (target: VeilRunOut): Promise<VeilRunOut | null> => {
      if (!token) return null;
      try {
        const claimed = await claimRun(token, target.id);
        setRun(claimed);
        if (claimed.result !== null) {
          if (!resolvedRef.current) {
            resolvedRef.current = true;
            refetch();
          }
          setPhase("resolved");
        }
        return claimed;
      } catch (err) {
        setMessage(errorMessage(err, "Failed to claim the reward."));
        setPhase("error");
        return null;
      }
    },
    [token, refetch],
  );

  useEffect(() => {
    if (phase !== "resolving") return;
    let cancelled = false;
    const target = run;

    (async () => {
      for (let attempt = 0; attempt < MAX_CLAIM_RETRIES; attempt++) {
        const claimed = await attemptClaim(target);
        if (cancelled || claimed === null) return;
        if (claimed.result !== null) return;
        await new Promise((resolve) => setTimeout(resolve, RETRY_DELAY_MS));
      }
      if (!cancelled) {
        setMessage("The veil hasn't released its verdict yet. Try again.");
        setPhase("error");
      }
    })();

    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [phase]);

  const encounter = run.encounter;
  const hasEnemy = !!encounter?.monster_name;

  return (
    <div className="combat-overlay">
      {phase === "waiting" && (
        <>
          <p className="combat-overlay-timer">
            {formatCountdown(Math.max(0, Math.ceil(msRemaining(run) / 1000)))}
          </p>
          <div className="combat-columns">
            <div className="combat-panel">
              {hero && (
                <>
                  <h2>{hero.name}</h2>
                  <CombatPanelArt src="/heroes/placeholder.svg" alt={hero.name} />
                  <p className="hero-meta">Level {hero.level}</p>
                  <ProgressBar value={hero.current_hp} max={hero.max_hp} variant="hp" />
                  <p className="hero-meta">
                    {hero.current_hp}/{hero.max_hp} HP
                  </p>
                  <table className="stat-table">
                    <tbody>
                      <tr>
                        <td>Damage</td>
                        <td>{formatRange(hero.damage_min, hero.damage_max)}</td>
                      </tr>
                      <tr>
                        <td>Spell Damage</td>
                        <td>{formatRange(hero.spell_damage_min, hero.spell_damage_max)}</td>
                      </tr>
                      <tr>
                        <td>Shield Defense</td>
                        <td>{hero.defense_shield}</td>
                      </tr>
                      <tr>
                        <td>Armor Defense</td>
                        <td>{hero.defense_armor}</td>
                      </tr>
                      <tr>
                        <td>Helmet Defense</td>
                        <td>{hero.defense_helmet}</td>
                      </tr>
                      {STAT_ORDER.map((row) => (
                        <tr key={row.key}>
                          <td>{row.label}</td>
                          <td>{hero[row.key]}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </>
              )}
            </div>

            <div className="combat-vs">VERSUS</div>

            <div className="combat-panel">
              {hasEnemy && encounter ? (
                <>
                  <h2>{encounter.monster_name}</h2>
                  <CombatPanelArt
                    src={`/monsters/${encounter.monster_slug}.svg`}
                    alt={encounter.monster_name ?? "enemy"}
                  />
                  <p className="hero-meta">
                    {formatLevelRange(encounter.monster_level_min, encounter.monster_level_max)}
                  </p>
                  <ProgressBar
                    value={encounter.monster_max_hp ?? 0}
                    max={encounter.monster_max_hp ?? 0}
                    variant="hp"
                  />
                  <p className="hero-meta">
                    {encounter.monster_max_hp}/{encounter.monster_max_hp} HP
                  </p>
                  <table className="stat-table">
                    <tbody>
                      <tr>
                        <td>Damage</td>
                        <td>
                          {formatRange(
                            encounter.monster_damage_min ?? 0,
                            encounter.monster_damage_max ?? 0,
                          )}
                        </td>
                      </tr>
                      <tr>
                        <td>Spell Damage</td>
                        <td>
                          {formatRange(
                            encounter.monster_spell_damage_min ?? 0,
                            encounter.monster_spell_damage_max ?? 0,
                          )}
                        </td>
                      </tr>
                      <tr>
                        <td>Shield Defense</td>
                        <td>{encounter.monster_defense ?? 0}</td>
                      </tr>
                      <tr>
                        <td>Armor Defense</td>
                        <td>—</td>
                      </tr>
                      <tr>
                        <td>Helmet Defense</td>
                        <td>—</td>
                      </tr>
                      {STAT_ORDER.map((row) => (
                        <tr key={row.key}>
                          <td>{row.label}</td>
                          <td>{encounter.monster_stats?.[row.key] ?? "—"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </>
              ) : (
                <p>Nothing stirred in the veil this time.</p>
              )}
            </div>
          </div>
        </>
      )}

      {phase === "resolving" && (
        <>
          <p>The veil is settling…</p>
          <button type="button" onClick={() => attemptClaim(run)}>
            Claim Reward
          </button>
        </>
      )}

      {phase === "resolved" && run.result && <CombatResultView run={run} onExit={onExit} />}

      {phase === "error" && (
        <>
          <p className="auth-error">{message}</p>
          <button type="button" onClick={() => attemptClaim(run)}>
            Retry
          </button>
        </>
      )}
    </div>
  );
}

function CombatResultView({ run, onExit }: { run: VeilRunOut; onExit: () => void }) {
  const result = run.result!;
  const monsterLabel = result.monster_name ?? "something in the veil";
  const skippedSlugs = new Set(result.loot_skipped.map(lootItemSlug));
  const keptLoot = result.loot.filter((entry) => !skippedSlugs.has(lootItemSlug(entry)));

  return (
    <div className="combat-result">
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
      {result.material_loot.length > 0 && (
        <p className="veil-loot-note">
          You also gathered: {result.material_loot.map(materialLootName).join(", ")}.
        </p>
      )}
      <button type="button" onClick={onExit}>
        EXIT THE VEIL
      </button>
    </div>
  );
}
