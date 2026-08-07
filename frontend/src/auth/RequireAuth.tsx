import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "./AuthContext";

export function RequireAuth() {
  const { token, loading } = useAuth();

  if (loading) return <div className="full-page-status">Loading…</div>;
  if (!token) return <Navigate to="/login" replace />;

  return <Outlet />;
}
