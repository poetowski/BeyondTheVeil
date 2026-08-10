import { useCallback, useEffect, useState } from "react";
import { enterCampaignNode, getCampaignChapters, getCampaignNodes } from "../api/campaign";
import { ApiError } from "../api/client";
import type { CampaignChapterOut, CampaignNodeOut } from "../api/types";
import { useAuth } from "../auth/AuthContext";
import { useVeilRun } from "../veil/VeilRunContext";

type State =
  | { kind: "loading" }
  | { kind: "loaded"; chapters: CampaignChapterOut[]; nodes: CampaignNodeOut[] }
  | { kind: "error"; message: string };

function statusLabel(status: CampaignNodeOut["status"]): string {
  switch (status) {
    case "cleared":
      return "Cleared";
    case "available":
      return "Available";
    case "locked":
      return "Locked";
  }
}

export function CampaignPage() {
  const { token, hero } = useAuth();
  const { startRun } = useVeilRun();
  const [state, setState] = useState<State>({ kind: "loading" });
  const [entering, setEntering] = useState<string | null>(null);
  const [enterError, setEnterError] = useState<string | null>(null);
  const [expandedChapters, setExpandedChapters] = useState<Set<string> | null>(null);

  const load = useCallback(async () => {
    if (!token) return;
    setState({ kind: "loading" });
    try {
      const [chapters, nodes] = await Promise.all([getCampaignChapters(token), getCampaignNodes(token)]);
      setState({ kind: "loaded", chapters, nodes });
      setExpandedChapters((prev) => prev ?? new Set(chapters.slice(0, 1).map((c) => c.id)));
    } catch (err) {
      setState({
        kind: "error",
        message: err instanceof ApiError ? err.message : "Failed to load the campaign.",
      });
    }
  }, [token]);

  useEffect(() => {
    load();
  }, [load]);

  function toggleChapter(chapterId: string) {
    setExpandedChapters((prev) => {
      const next = new Set(prev ?? []);
      if (next.has(chapterId)) {
        next.delete(chapterId);
      } else {
        next.add(chapterId);
      }
      return next;
    });
  }

  async function handleEnter(node: CampaignNodeOut) {
    if (!token) return;
    setEnterError(null);
    setEntering(node.id);
    try {
      const run = await enterCampaignNode(token, node.id);
      startRun(run);
    } catch (err) {
      setEnterError(err instanceof ApiError ? err.message : "Failed to enter this battle.");
    } finally {
      setEntering(null);
    }
  }

  return (
    <div className="page">
      <h1>Campaign</h1>
      {state.kind === "loading" && <p>Charting the path ahead…</p>}
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
          {state.chapters.length === 0 ? (
            <p>No campaign battles have been charted yet.</p>
          ) : (
            state.chapters.map((chapter) => {
              const nodes = state.nodes
                .filter((node) => node.chapter_id === chapter.id)
                .sort((a, b) => a.order_index - b.order_index);
              const expanded = expandedChapters?.has(chapter.id) ?? false;
              return (
                <section key={chapter.id} className="campaign-chapter">
                  <button
                    type="button"
                    className="campaign-chapter-header"
                    aria-expanded={expanded}
                    onClick={() => toggleChapter(chapter.id)}
                  >
                    <span>{expanded ? "▾" : "▸"}</span>
                    <span className="campaign-chapter-title">{chapter.title}</span>
                  </button>
                  {expanded && (
                    <ul className="campaign-list campaign-chapter-body">
                      {nodes.map((node) => {
                        const canEnter =
                          node.status === "available" && !!hero && hero.level >= node.required_level;
                        return (
                          <li key={node.id} className={`campaign-node campaign-node-${node.status}`}>
                            <div className="campaign-node-header">
                              <span className="campaign-node-name">
                                {node.order_index}. {node.name}
                              </span>
                              <span className={`campaign-node-badge campaign-node-badge-${node.status}`}>
                                {statusLabel(node.status)}
                              </span>
                            </div>
                            <p className="campaign-node-meta">
                              vs {node.monster_name} · requires level {node.required_level}
                            </p>
                            {node.status === "available" && (
                              <button
                                type="button"
                                disabled={!canEnter || entering === node.id}
                                onClick={() => handleEnter(node)}
                              >
                                {entering === node.id ? "Entering…" : "Enter Battle"}
                              </button>
                            )}
                          </li>
                        );
                      })}
                    </ul>
                  )}
                </section>
              );
            })
          )}
          {enterError && <p className="auth-error">{enterError}</p>}
        </>
      )}
    </div>
  );
}
