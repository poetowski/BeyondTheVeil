import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getAvatars } from "../api/avatars";
import { ApiError } from "../api/client";
import { setAvatar } from "../api/hero";
import type { AvatarTemplateOut } from "../api/types";
import { useAuth } from "../auth/AuthContext";

type State =
  | { kind: "loading" }
  | { kind: "loaded"; avatars: AvatarTemplateOut[] }
  | { kind: "error"; message: string };

function AvatarCardImage({ avatar }: { avatar: AvatarTemplateOut }) {
  const [missing, setMissing] = useState(false);

  if (missing) {
    return <div className="avatar-card-image avatar-card-image--missing" aria-hidden="true" />;
  }

  return (
    <img
      className="avatar-card-image"
      src={`/heroes/${avatar.slug}.svg`}
      alt={avatar.name}
      onError={() => setMissing(true)}
    />
  );
}

export function AvatarPage() {
  const { token, hero, refetch } = useAuth();
  const navigate = useNavigate();
  const [state, setState] = useState<State>({ kind: "loading" });
  const [selectedSlug, setSelectedSlug] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!token) return;
    setState({ kind: "loading" });
    try {
      const avatars = await getAvatars(token);
      setState({ kind: "loaded", avatars });
    } catch (err) {
      setState({
        kind: "error",
        message: err instanceof ApiError ? err.message : "Failed to load avatars.",
      });
    }
  }, [token]);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    if (hero && selectedSlug === null) {
      setSelectedSlug(hero.avatar_slug);
    }
  }, [hero, selectedSlug]);

  async function handleSave() {
    if (!token || !selectedSlug) return;
    setSaving(true);
    setSaveError(null);
    try {
      await setAvatar(token, selectedSlug);
      await refetch();
      navigate("/overview");
    } catch (err) {
      setSaveError(err instanceof ApiError ? err.message : "Failed to save avatar.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="page">
      <h1>Change Avatar</h1>
      {state.kind === "loading" && <p>Loading avatars…</p>}
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
          <div className="avatar-grid">
            {state.avatars.map((avatar) => (
              <button
                type="button"
                key={avatar.id}
                className={
                  "avatar-card" + (selectedSlug === avatar.slug ? " avatar-card--selected" : "")
                }
                onClick={() => setSelectedSlug(avatar.slug)}
              >
                <AvatarCardImage avatar={avatar} />
                <span className="avatar-card-name">{avatar.name}</span>
              </button>
            ))}
          </div>
          {saveError && <p className="auth-error">{saveError}</p>}
          <button type="button" onClick={handleSave} disabled={saving || !selectedSlug}>
            {saving ? "Saving…" : "Save"}
          </button>
        </>
      )}
    </div>
  );
}
