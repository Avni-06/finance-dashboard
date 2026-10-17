import { NavLink, Outlet, Link, useNavigate } from "react-router-dom";
import {
  LayoutDashboard, ReceiptText, PiggyBank, Target, Sparkles, Settings, ShieldCheck,
  LogOut, Moon, Sun,
} from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { useTheme } from "../lib/useTheme";
import { Logo } from "./ui";
import { PROFILE_LABELS } from "../lib/format";

const USER_NAV = [
  { to: "/app", label: "Overview", icon: LayoutDashboard, end: true },
  { to: "/app/transactions", label: "Transactions", icon: ReceiptText },
  { to: "/app/budgets", label: "Budgets", icon: PiggyBank },
  { to: "/app/goals", label: "Goals", icon: Target },
  { to: "/app/insights", label: "Weekly report", icon: Sparkles },
];

function NavItem({ to, label, icon: Icon, end, compact }) {
  return (
    <NavLink
      to={to}
      end={end}
      className={({ isActive }) =>
        compact
          ? `flex flex-col items-center gap-0.5 px-2 py-1.5 text-[11px] font-semibold rounded-md ${
              isActive ? "text-accent" : "text-muted"
            }`
          : `flex items-center gap-3 px-3 h-10 rounded-lg text-sm font-semibold transition-colors ${
              isActive ? "bg-raised text-ink" : "text-muted hover:text-ink hover:bg-raised/60"
            }`
      }
    >
      {({ isActive }) => (
        <>
          <Icon size={compact ? 20 : 18} className={isActive && !compact ? "text-accent" : ""} aria-hidden="true" />
          <span>{label}</span>
        </>
      )}
    </NavLink>
  );
}

export default function Layout() {
  const { user, isDemo, isAdmin, logout } = useAuth();
  const { theme, toggle } = useTheme();
  const navigate = useNavigate();
  const nav = isAdmin
    ? [{ to: "/app/admin", label: "Admin", icon: ShieldCheck, end: true }]
    : USER_NAV;

  const signOut = () => {
    logout();
    navigate("/");
  };

  return (
    <div className="min-h-screen lg:grid lg:grid-cols-[240px_1fr]">
      {/* Sidebar (desktop) */}
      <aside className="hidden lg:flex flex-col border-r border-line bg-surface/60 px-4 py-5 sticky top-0 h-screen">
        <Link to="/app" className="px-2 mb-7"><Logo /></Link>
        <nav className="flex flex-col gap-1" aria-label="Main">
          {nav.map((n) => <NavItem key={n.to} {...n} />)}
          <NavItem to="/app/settings" label="Settings" icon={Settings} />
        </nav>
        <div className="mt-auto space-y-3">
          <div className="px-3 py-3 rounded-lg bg-raised/60">
            <p className="text-sm font-semibold truncate">{user?.name}</p>
            <p className="text-xs text-muted">
              {isAdmin ? "Administrator" : `${PROFILE_LABELS[user?.profile_type] || "User"}${isDemo ? " demo" : ""}`}
            </p>
          </div>
          <div className="flex gap-1">
            <button className="btn-ghost flex-1 h-9" onClick={toggle} aria-label="Toggle theme">
              {theme === "dark" ? <Sun size={16} /> : <Moon size={16} />}
              {theme === "dark" ? "Light" : "Dark"}
            </button>
            <button className="btn-ghost flex-1 h-9" onClick={signOut}>
              <LogOut size={16} /> Log out
            </button>
          </div>
        </div>
      </aside>

      <div className="min-w-0 flex flex-col">
        {/* Top bar (mobile) */}
        <header className="lg:hidden flex items-center justify-between px-4 h-14 border-b border-line bg-surface/80 backdrop-blur sticky top-0 z-30">
          <Link to="/app"><Logo /></Link>
          <div className="flex items-center gap-1">
            <button className="btn-ghost h-9 w-9 px-0" onClick={toggle} aria-label="Toggle theme">
              {theme === "dark" ? <Sun size={18} /> : <Moon size={18} />}
            </button>
            <Link to="/app/settings" className="btn-ghost h-9 w-9 px-0" aria-label="Settings"><Settings size={18} /></Link>
            <button className="btn-ghost h-9 w-9 px-0" onClick={signOut} aria-label="Log out"><LogOut size={18} /></button>
          </div>
        </header>

        {isDemo && (
          <div className="bg-accent/10 border-b border-accent/30 px-4 sm:px-8 py-2.5 text-sm flex flex-wrap items-center gap-x-3 gap-y-1">
            <span>
              You're exploring a read-only demo with sample data.
            </span>
            <button className="font-semibold underline underline-offset-2" onClick={() => { logout(); navigate("/register"); }}>
              Create your own account
            </button>
          </div>
        )}

        <main className="flex-1 px-4 sm:px-8 py-6 pb-28 lg:pb-10 max-w-[1240px] w-full mx-auto">
          <Outlet />
        </main>
      </div>

      {/* Bottom tabs (mobile) */}
      <nav
        aria-label="Main"
        className="lg:hidden fixed bottom-0 inset-x-0 z-30 border-t border-line bg-surface/95 backdrop-blur flex justify-around px-1 pb-[env(safe-area-inset-bottom)]"
      >
        {nav.map((n) => <NavItem key={n.to} {...n} compact label={n.label === "Weekly report" ? "Report" : n.label} />)}
      </nav>
    </div>
  );
}
