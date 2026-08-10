import { Outlet } from "react-router-dom";
import { CombatOverlay } from "../veil/CombatOverlay";
import { VeilRunProvider, useVeilRun } from "../veil/VeilRunContext";
import { Sidebar } from "./Sidebar";
import "./AppLayout.css";

function AppLayoutInner() {
  const { activeRun, clearRun } = useVeilRun();

  return (
    <div className="app-layout">
      <Sidebar />
      <main className="app-content">
        <Outlet />
      </main>
      {activeRun && <CombatOverlay run={activeRun} onExit={clearRun} />}
    </div>
  );
}

export function AppLayout() {
  return (
    <VeilRunProvider>
      <AppLayoutInner />
    </VeilRunProvider>
  );
}
