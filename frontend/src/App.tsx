import { Navigate, Route, Routes } from "react-router-dom";
import { RequireAuth } from "./auth/RequireAuth";
import { AppLayout } from "./layout/AppLayout";
import { BackpackPage } from "./pages/BackpackPage";
import { ConceptPage } from "./pages/ConceptPage";
import { HeroPage } from "./pages/HeroPage";
import { LoginPage } from "./pages/LoginPage";
import { SignupPage } from "./pages/SignupPage";
import { VeilPage } from "./pages/VeilPage";

function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/signup" element={<SignupPage />} />

      <Route element={<RequireAuth />}>
        <Route element={<AppLayout />}>
          <Route path="/hero" element={<HeroPage />} />
          <Route path="/backpack" element={<BackpackPage />} />
          <Route path="/veil" element={<VeilPage />} />
          <Route path="/concept" element={<ConceptPage />} />
        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/hero" replace />} />
    </Routes>
  );
}

export default App;
