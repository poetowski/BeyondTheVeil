import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

interface NavItem {
  to: string;
  label: string;
  children?: NavItem[];
  /** Visually distinguishes this one link from the rest of the nav. */
  highlight?: boolean;
}

// Hero is the only top-level item with a dedicated screen of its own -
// The Veil and Crafting instead forward straight to their first sub-tab
// (Campaign, Alchemy) when clicked, same as clicking a folder opens the
// first thing inside it.
const NAV_ITEMS: NavItem[] = [
  {
    to: "/hero",
    label: "Hero",
    children: [
      { to: "/backpack", label: "Backpack" },
      { to: "/materials", label: "Materials" },
    ],
  },
  {
    to: "/campaign",
    label: "The Veil",
    highlight: true,
    children: [
      { to: "/campaign", label: "Campaign" },
      { to: "/bestiary", label: "Bestiary" },
    ],
  },
  {
    to: "/alchemy",
    label: "Crafting",
    children: [
      { to: "/alchemy", label: "Alchemy" },
      { to: "/forge", label: "Forge" },
    ],
  },
  { to: "/concept", label: "Concept" },
];

function navLinkClass(highlight?: boolean) {
  return ({ isActive }: { isActive: boolean }): string =>
    "sidebar-nav-link" + (isActive ? " active" : "") + (highlight ? " veil-highlight" : "");
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
            <NavLink to={item.to} className={navLinkClass(item.highlight)} end={!!item.children}>
              {item.label}
            </NavLink>
            {item.children && (
              <div className="sidebar-subnav">
                {item.children.map((child) => (
                  <NavLink key={child.to} to={child.to} className={navLinkClass(child.highlight)}>
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
