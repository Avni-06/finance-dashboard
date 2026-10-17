import { useEffect, useState } from "react";

const KEY = "finsight-theme";
const root = document.documentElement;

/** Theme lives on <html data-theme>. Every hook instance watches it, so
 *  toggling from Settings also updates the sidebar button. */
export function useTheme() {
  const [theme, setThemeState] = useState(() => root.dataset.theme || "dark");

  useEffect(() => {
    const obs = new MutationObserver(() => setThemeState(root.dataset.theme || "dark"));
    obs.observe(root, { attributes: true, attributeFilter: ["data-theme"] });
    return () => obs.disconnect();
  }, []);

  const setTheme = (t) => {
    root.dataset.theme = t;
    try { localStorage.setItem(KEY, t); } catch { /* private mode */ }
  };

  return { theme, setTheme, toggle: () => setTheme(theme === "dark" ? "light" : "dark") };
}
