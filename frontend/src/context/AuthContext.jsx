import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { api, tokenStore } from "../lib/api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(Boolean(tokenStore.get()));

  const refresh = useCallback(async () => {
    if (!tokenStore.get()) {
      setUser(null);
      setLoading(false);
      return null;
    }
    try {
      const { user } = await api.get("/auth/me");
      setUser(user);
      return user;
    } catch {
      tokenStore.clear();
      setUser(null);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
    const onLogout = () => setUser(null);
    window.addEventListener("finsight:logout", onLogout);
    return () => window.removeEventListener("finsight:logout", onLogout);
  }, [refresh]);

  const startSession = ({ token, user }) => {
    tokenStore.set(token);
    setUser(user);
    return user;
  };

  const value = {
    user,
    loading,
    isDemo: user?.role === "demo",
    isAdmin: user?.role === "admin",
    login: async (email, password) => startSession(await api.post("/auth/login", { email, password })),
    register: async (body) => startSession(await api.post("/auth/register", body)),
    demo: async (profile_type) => startSession(await api.post("/auth/demo", { profile_type })),
    logout: () => {
      tokenStore.clear();
      setUser(null);
    },
    setUser,
    refresh,
  };
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export const useAuth = () => useContext(AuthContext);
