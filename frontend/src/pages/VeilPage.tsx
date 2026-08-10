import { useState } from "react";
import { ApiError } from "../api/client";
import { enterVeil } from "../api/veil";
import { useAuth } from "../auth/AuthContext";
import { useVeilRun } from "../veil/VeilRunContext";

export function VeilPage() {
  const { token } = useAuth();
  const { activeRun, startRun } = useVeilRun();
  const [error, setError] = useState<string | null>(null);
  const [entering, setEntering] = useState(false);

  async function handleEnter() {
    if (!token) return;
    setError(null);
    setEntering(true);
    try {
      const run = await enterVeil(token);
      startRun(run);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to start a jump.");
    } finally {
      setEntering(false);
    }
  }

  return (
    <div className="page">
      <h1>Jumpins</h1>
      {activeRun ? (
        <p>Your hero is already mid-jump.</p>
      ) : (
        <>
          <p>Take a jump when you're ready.</p>
          <button type="button" disabled={entering} onClick={handleEnter}>
            {entering ? "Jumping…" : "Jump In"}
          </button>
        </>
      )}
      {error && <p className="auth-error">{error}</p>}
    </div>
  );
}
