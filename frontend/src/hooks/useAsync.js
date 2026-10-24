import { useCallback, useEffect, useState } from "react";

// Runs an async loader on mount and gives { data, error, loading, reload }.
export function useAsync(fn, deps = []) {
  const [state, setState] = useState({ data: null, error: "", loading: true });
  const run = useCallback(async () => {
    try {
      const data = await fn();
      setState({ data, error: "", loading: false });
    } catch (e) {
      setState((s) => ({ ...s, error: e.message, loading: false }));
    }
  }, deps); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => { run(); }, [run]);
  return { ...state, reload: run };
}
