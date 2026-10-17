import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "./api";

/** GET a path; re-runs when the path changes. Returns { data, error, loading, reload }. */
export function useFetch(path) {
  const [state, setState] = useState({ data: null, error: null, loading: true });
  const latest = useRef(path);

  const load = useCallback(async () => {
    if (!path) return;
    latest.current = path;
    setState((s) => ({ ...s, loading: true, error: null }));
    try {
      const data = await api.get(path);
      if (latest.current === path) setState({ data, error: null, loading: false });
    } catch (error) {
      if (latest.current === path) setState((s) => ({ ...s, error, loading: false }));
    }
  }, [path]);

  useEffect(() => { load(); }, [load]);
  return { ...state, reload: load };
}
