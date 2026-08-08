import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

const NAV_ITEMS = [
  {
    to: "/hero",
    label: "Hero",
    children: [
      { to: "/backpack", label: "Backpack" },
      { to: "/materials", label: "Materials" },
    ],
  },
  {
    to: "/veil",
    label: "The Veil",
    children: [
      { to: "/campaign", label: "Campaign" },
      { to: "/bestiary", label: "Bestiary" },
    ],
  },
  { to: "/concept", label: "Concept" },
];

function navLinkClass({ isActive }: { isActive: boolean }): string {
  return "sidebar-nav-link" + (isActive ? " active" : "");
}

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
          <div key={item.to} className="sidebar-nav-group">
            <NavLink to={item.to} className={navLinkClass} end={!!item.children}>
              {item.label}
            </NavLink>
            {item.children && (
              <div className="sidebar-subnav">
                {item.children.map((child) => (
                  <NavLink key={child.to} to={child.to} className={navLinkClass}>
                    {child.label}
                  </NavLink>
                ))}
              </div>
            )}
          </div>
        ))}
      </nav>

      <button type="button" className="sidebar-logout" onClick={handleLogout}>
        Logout
      </button>
    </aside>
  );
}
