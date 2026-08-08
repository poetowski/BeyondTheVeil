import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

const NAV_ITEMS = [
  { to: "/hero", label: "Hero" },
  { to: "/backpack", label: "Backpack" },
  { to: "/veil", label: "The Veil" },
  { to: "/concept", label: "Concept" },
];

export function Sidebar() {
  const { hero, logout } = useAuth();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate("/login", { replace: true });
  }

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <span className="sidebar-title">Beyond the Veil</span>
        {hero && <span className="sidebar-hero-name">{hero.name}</span>}
      </div>

      <nav className="sidebar-nav">
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) => "sidebar-nav-link" + (isActive ? " active" : "")}
          >
            {item.label}
          </NavLink>
        ))}
      </nav>

      <button type="button" className="sidebar-logout" onClick={handleLogout}>
        Logout
      </button>
    </aside>
  );
}
