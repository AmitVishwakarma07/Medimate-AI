import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { api, setUnauthorizedHandler } from "../services/api";

const AuthCtx = createContext(null);
export const useAuth = () => useContext(AuthCtx);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Clears the screen state only (used when the server says the session is gone).
  const clearSession = useCallback(() => {
    setUser(null);
    window.location.hash = "";
  }, []);

  // Asks the server to end the session (it removes the cookie), then clears the screen.
  const logout = useCallback(async () => {
    try { await api.logout(); } catch { /* ignore: we are leaving anyway */ }
    clearSession();
  }, [clearSession]);

  useEffect(() => {
    setUnauthorizedHandler(clearSession);
    // If a valid session cookie exists, this restores the logged-in user.
    api.profile().then(setUser).catch(() => {}).finally(() => setLoading(false));
  }, [clearSession]);

  const authenticate = async (fn, payload) => {
    const r = await fn(payload);
    setUser(r.user);
  };

  return (
    <AuthCtx.Provider value={{
      user, setUser, loading, logout, clearSession,
      login: (p) => authenticate(api.login, p),
      register: (p) => authenticate(api.register, p),
    }}>
      {children}
    </AuthCtx.Provider>
  );
}
