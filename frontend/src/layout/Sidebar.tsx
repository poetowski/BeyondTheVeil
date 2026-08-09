import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

interface NavItem {
  to: string;
  label: string;
  children?: NavItem[];
  /** False for group headers that have no page of their own (e.g. "Crafting"
   * only organizes Alchemy/Forge) - rendered as plain text instead of a link. */
  hasPage?: boolean;
  /** Visually distinguishes this one link from the rest of the nav. */
  highlight?: boolean;
}

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
    to: "/veil",
    label: "The Veil",
    highlight: true,
    children: [
      { to: "/campaign", label: "Campaign" },
      { to: "/bestiary", label: "Bestiary" },
    ],
  },
  {
    to: "/crafting",
    label: "Crafting",
    hasPage: false,
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
            {item.hasPage === false ? (
              <span
                className={"sidebar-nav-group-label" + (item.highlight ? " veil-highlight" : "")}
              >
                {item.label}
              </span>
            ) : (
              <NavLink to={item.to} className={navLinkClass(item.highlight)} end={!!item.children}>
                {item.label}
              </NavLink>
            )}
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
