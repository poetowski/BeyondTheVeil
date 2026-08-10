import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import type { VeilRunOut } from "../api/types";
import { getActiveRun } from "../api/veil";
import { useAuth } from "../auth/AuthContext";

interface VeilRunContextValue {
  activeRun: VeilRunOut | null;
  startRun: (run: VeilRunOut) => void;
  clearRun: () => void;
}

const VeilRunContext = createContext<VeilRunContextValue | undefined>(undefined);

export function VeilRunProvider({ children }: { children: ReactNode }) {
  const { token } = useAuth();
  const [activeRun, setActiveRun] = useState<VeilRunOut | null>(null);

  // Resumes an in-progress run after a page reload. No polling beyond this -
  // every run this client doesn't already know about was either just
  // created by startRun() below or predates this session (caught here).
  useEffect(() => {
    if (!token) {
      setActiveRun(null);
      return;
    }
    let cancelled = false;
    getActiveRun(token).then((run) => {
      if (!cancelled) setActiveRun(run);
    });
    return () => {
      cancelled = true;
    };
  }, [token]);

  return (
    <VeilRunContext.Provider
      value={{
        activeRun,
        startRun: setActiveRun,
        clearRun: () => setActiveRun(null),
      }}
    >
      {children}
    </VeilRunContext.Provider>
  );
}

export function useVeilRun(): VeilRunContextValue {
  const ctx = useContext(VeilRunContext);
  if (!ctx) throw new Error("useVeilRun must be used within a VeilRunProvider");
  return ctx;
}
