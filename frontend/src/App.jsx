import { Navigate, Route, Routes, Link } from "react-router-dom";
import { useAuth } from "./context/AuthContext";
import Layout from "./components/Layout";
import Landing from "./pages/Landing";
import { Login, Register } from "./pages/Auth";
import Onboarding from "./pages/Onboarding";
import Dashboard from "./pages/Dashboard";
import Transactions from "./pages/Transactions";
import Budgets from "./pages/Budgets";
import Goals from "./pages/Goals";
import Insights from "./pages/Insights";
import Settings from "./pages/Settings";
import Admin from "./pages/Admin";
import { Logo } from "./components/ui";

function FullScreenLoader() {
  return (
    <div className="min-h-screen grid place-items-center">
      <div className="animate-pulse"><Logo /></div>
    </div>
  );
}

/** Route guard: login required, optional role list, onboarding first for new users. */
function Protected({ children, roles }) {
  const { user, loading } = useAuth();
  if (loading) return <FullScreenLoader />;
  if (!user) return <Navigate to="/login" replace />;
  if (roles && !roles.includes(user.role)) return <Navigate to={user.role === "admin" ? "/app/admin" : "/app"} replace />;
  if (user.role === "user" && !user.onboarded) return <Navigate to="/onboarding" replace />;
  return children;
}

function GuestOnly({ children }) {
  const { user, loading } = useAuth();
  if (loading) return <FullScreenLoader />;
  if (user) return <Navigate to={user.role === "admin" ? "/app/admin" : "/app"} replace />;
  return children;
}

function NotFound() {
  return (
    <div className="min-h-screen grid place-items-center px-4 text-center">
      <div>
        <Logo />
        <h1 className="text-3xl font-bold mt-6">This page doesn't exist</h1>
        <p className="text-muted mt-2">The link may be broken or the page was moved.</p>
        <Link to="/" className="btn-primary mt-6">Go to FinSight</Link>
      </div>
    </div>
  );
}

const USER_ROLES = ["user", "demo"];

export default function App() {
  const { user, loading } = useAuth();
  return (
    <Routes>
      <Route path="/" element={loading ? <FullScreenLoader /> : <Landing />} />
      <Route path="/login" element={<GuestOnly><Login /></GuestOnly>} />
      <Route path="/register" element={<GuestOnly><Register /></GuestOnly>} />
      <Route
        path="/onboarding"
        element={loading ? <FullScreenLoader /> : !user ? <Navigate to="/login" replace />
          : user.onboarded || user.role !== "user" ? <Navigate to="/app" replace /> : <Onboarding />}
      />
      <Route path="/app" element={<Protected><Layout /></Protected>}>
        <Route index element={<Protected roles={USER_ROLES}><Dashboard /></Protected>} />
        <Route path="transactions" element={<Protected roles={USER_ROLES}><Transactions /></Protected>} />
        <Route path="budgets" element={<Protected roles={USER_ROLES}><Budgets /></Protected>} />
        <Route path="goals" element={<Protected roles={USER_ROLES}><Goals /></Protected>} />
        <Route path="insights" element={<Protected roles={USER_ROLES}><Insights /></Protected>} />
        <Route path="settings" element={<Settings />} />
        <Route path="admin" element={<Protected roles={["admin"]}><Admin /></Protected>} />
      </Route>
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
}
