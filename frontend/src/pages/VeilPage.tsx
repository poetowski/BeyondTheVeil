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
      setError(err instanceof ApiError ? err.message : "Failed to enter the veil.");
    } finally {
      setEntering(false);
    }
  }

  return (
    <div className="page">
      <h1>The Veil</h1>
      {activeRun ? (
        <p>Your hero is already inside the veil.</p>
      ) : (
        <>
          <p>The veil is still. Step through when you're ready.</p>
          <button type="button" disabled={entering} onClick={handleEnter}>
            {entering ? "Entering…" : "Enter the Veil"}
          </button>
        </>
      )}
      {error && <p className="auth-error">{error}</p>}
    </div>
  );
}
