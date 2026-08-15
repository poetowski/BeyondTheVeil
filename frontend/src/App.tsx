import { Navigate, Route, Routes } from "react-router-dom";
import { RequireAuth } from "./auth/RequireAuth";
import { AppLayout } from "./layout/AppLayout";
import { AlchemyPage } from "./pages/AlchemyPage";
import { BackpackPage } from "./pages/BackpackPage";
import { BestiaryPage } from "./pages/BestiaryPage";
import { ConceptPage } from "./pages/ConceptPage";
import { CraftingPage } from "./pages/CraftingPage";
import { ForgePage } from "./pages/ForgePage";
import { LeaderboardPage } from "./pages/LeaderboardPage";
import { LoginPage } from "./pages/LoginPage";
import { MaterialsPage } from "./pages/MaterialsPage";
import { OverviewPage } from "./pages/OverviewPage";
import { ShopPage } from "./pages/ShopPage";
import { SignupPage } from "./pages/SignupPage";
import { VeilPage } from "./pages/VeilPage";

function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/signup" element={<SignupPage />} />

      <Route element={<RequireAuth />}>
        <Route element={<AppLayout />}>
          <Route path="/overview" element={<OverviewPage />} />
          <Route path="/backpack" element={<BackpackPage />} />
          <Route path="/materials" element={<MaterialsPage />} />
          <Route path="/crafting" element={<CraftingPage />} />
          <Route path="/alchemy" element={<AlchemyPage />} />
          <Route path="/forge" element={<ForgePage />} />
          <Route path="/veil" element={<VeilPage />} />
          <Route path="/bestiary" element={<BestiaryPage />} />
          <Route path="/shop" element={<ShopPage />} />
          <Route path="/leaderboard" element={<LeaderboardPage />} />
          <Route path="/concept" element={<ConceptPage />} />
        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/overview" replace />} />
    </Routes>
  );
}

export default App;
