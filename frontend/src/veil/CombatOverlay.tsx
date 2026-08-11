import { useCallback, useEffect, useRef, useState } from "react";
import type { StatName, VeilRunOut } from "../api/types";
import { claimRun, getActiveRun } from "../api/veil";
import { useAuth } from "../auth/AuthContext";
import { ProgressBar } from "../components/ProgressBar";
import "./CombatOverlay.css";

const MAX_REVEAL_RETRIES = 5;
const RETRY_DELAY_MS = 1000;

const STAT_ORDER: { key: StatName; label: string }[] = [
  { key: "strength", label: "Strength" },
  { key: "dexterity", label: "Dexterity" },
  { key: "intelligence", label: "Intelligence" },
  { key: "vitality", label: "Vitality" },
  { key: "agility", label: "Agility" },
  { key: "spirit", label: "Spirit" },
];

type Phase = "waiting" | "revealing" | "resolved";

function msRemaining(run: VeilRunOut): number {
  return new Date(run.resolves_at).getTime() - Date.now();
}

function nextPhase(run: VeilRunOut): Phase {
  // `result` becomes readable as soon as resolves_at passes, independent
  // of whether the run has been claimed yet (see is_visible/to_out) -
  // claiming only happens when the player clicks Exit The Veil below, so
  // "resolved" here just means "show the Combat Log," not "already claimed."
  if (run.result !== null) return "resolved";
  return msRemaining(run) <= 0 ? "revealing" : "waiting";
}

function formatCountdown(totalSeconds: number): string {
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes}:${seconds.toString().padStart(2, "0")}`;
}

function formatRange(min: number, max: number): string {
  return min === max ? `${min}` : `${min}-${max}`;
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

function formatLogEntry(entry: Record<string, unknown>, heroName: string, monsterName: string): string {
  const actor = entry.actor === "hero" ? heroName : monsterName;
  const defender = entry.actor === "hero" ? monsterName : heroName;
  const phaseLabel = entry.phase === "spell" ? "Opening cast" : `Round ${entry.round}`;

  if (!entry.hit) {
    return `${phaseLabel} — ${actor}'s attack misses.`;
  }

  const damage = entry.damage as number;
  const hpRemaining = entry.defender_hp_remaining as number;
  const zone = entry.zone as string | null | undefined;
  const hitDescription =
    zone === "helmet"
      ? `lands a headshot on ${defender}`
      : zone
        ? `hits ${defender}'s ${zone}`
        : `hits ${defender}`;

  return `${phaseLabel} — ${actor} ${hitDescription} for ${damage} damage (${hpRemaining} HP left).`;
}

interface CombatOverlayProps {
  run: VeilRunOut;
  onExit: () => void;
}

export function CombatOverlay({ run: incomingRun, onExit }: CombatOverlayProps) {
  const { token, hero, refetch } = useAuth();
  const [run, setRun] = useState(incomingRun);
  const [phase, setPhase] = useState<Phase>(() => nextPhase(incomingRun));
  const [revealFailed, setRevealFailed] = useState(false);
  const [exiting, setExiting] = useState(false);
  const [tick, setTick] = useState(0);
  const refetchedRef = useRef(false);

  // A different run arriving (a fresh "Enter the Veil" after the previous
  // one was exited) resets local state to match it.
  useEffect(() => {
    setRun(incomingRun);
    setPhase(nextPhase(incomingRun));
    setRevealFailed(false);
    refetchedRef.current = false;
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
      setPhase("revealing");
    }
  }, [phase, run, tick]);

  // Reveals the result once resolves_at passes - a read-only peek
  // (GET /veil/active already returns the result once visible, regardless
  // of claim status), never claims. Claiming only happens on Exit below.
  useEffect(() => {
    if (phase !== "revealing" || !token) return;
    let cancelled = false;

    (async () => {
      for (let attempt = 0; attempt < MAX_REVEAL_RETRIES; attempt++) {
        try {
          const active = await getActiveRun(token);
          if (cancelled) return;
          if (active && active.result !== null) {
            setRun(active);
            setPhase("resolved");
            return;
          }
        } catch {
          // fall through to retry
        }
        await new Promise((resolve) => setTimeout(resolve, RETRY_DELAY_MS));
      }
      if (!cancelled) setRevealFailed(true);
    })();

    return () => {
      cancelled = true;
    };
  }, [phase, token]);

  const handleExit = useCallback(async () => {
    if (!token || exiting) return;
    setExiting(true);
    try {
      await claimRun(token, run.id);
    } catch {
      // Best effort - an unclaimed-but-visible run self-heals the next
      // time it's loaded, so it's safe to leave anyway.
    }
    if (!refetchedRef.current) {
      refetchedRef.current = true;
      refetch();
    }
    onExit();
  }, [token, exiting, run.id, refetch, onExit]);

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
                  <p className="hero-meta">Level {encounter.monster_level}</p>
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
                        <td>Defense</td>
                        <td>{encounter.monster_defense ?? 0}</td>
                      </tr>
                      <tr>
                        <td>&nbsp;</td>
                        <td>&nbsp;</td>
                      </tr>
                      <tr>
                        <td>&nbsp;</td>
                        <td>&nbsp;</td>
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

      {phase === "revealing" && !revealFailed && <p>The veil is settling…</p>}

      {phase === "revealing" && revealFailed && (
        <>
          <p className="auth-error">The veil is taking longer than usual to settle.</p>
          <button type="button" disabled={exiting} onClick={handleExit}>
            {exiting ? "Exiting…" : "EXIT THE VEIL"}
          </button>
        </>
      )}

      {phase === "resolved" && run.result && (
        <CombatLogView run={run} exiting={exiting} onExit={handleExit} />
      )}
    </div>
  );
}

function CombatLogView({
  run,
  exiting,
  onExit,
}: {
  run: VeilRunOut;
  exiting: boolean;
  onExit: () => void;
}) {
  const { hero } = useAuth();
  const result = run.result!;
  const encounter = run.encounter;
  const monsterLabel = result.monster_name ?? "something in the veil";
  const skippedSlugs = new Set(result.loot_skipped.map(lootItemSlug));
  const keptLoot = result.loot.filter((entry) => !skippedSlugs.has(lootItemSlug(entry)));

  const heroMaxHp = hero?.max_hp ?? 0;
  const heroHpAfter = result.hero_hp_after ?? 0;
  const monsterMaxHp = encounter?.monster_max_hp ?? 0;
  const monsterHpAfter = result.monster_hp_after ?? 0;
  const damageDealt = Math.max(0, monsterMaxHp - monsterHpAfter);
  const damageTaken = Math.max(0, (result.hero_hp_before ?? heroMaxHp) - heroHpAfter);

  return (
    <div className="combat-log">
      <p className={result.victory ? "veil-victory" : "veil-defeat"}>
        {result.victory ? "Victory" : "Defeat"} against {monsterLabel}.
      </p>

      <div className="combat-log-hp-row">
        <div className="combat-log-hp-col">
          <p className="hero-meta">{hero?.name ?? "You"}</p>
          <ProgressBar value={heroHpAfter} max={heroMaxHp} variant="hp" />
          <p className="hero-meta">
            {heroHpAfter}/{heroMaxHp} HP
          </p>
        </div>
        <div className="combat-log-hp-col">
          <p className="hero-meta">{monsterLabel}</p>
          <ProgressBar value={monsterHpAfter} max={monsterMaxHp} variant="hp" />
          <p className="hero-meta">
            {monsterHpAfter}/{monsterMaxHp} HP
          </p>
        </div>
      </div>

      <div className="combat-log-summary">
        <span>Damage Dealt: {damageDealt}</span>
        <span>Damage Taken: {damageTaken}</span>
      </div>

      <div className="combat-log-list">
        {result.log.map((entry, index) => (
          <p key={index} className="combat-log-entry">
            {formatLogEntry(entry, hero?.name ?? "You", monsterLabel)}
          </p>
        ))}
      </div>

      <p className="veil-loot-note">
        You gained {result.xp_awarded} XP{result.gold_awarded > 0 ? ` and ${result.gold_awarded} gold` : ""}.
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
      <button type="button" disabled={exiting} onClick={onExit}>
        {exiting ? "Exiting…" : "EXIT THE VEIL"}
      </button>
    </div>
  );
}
