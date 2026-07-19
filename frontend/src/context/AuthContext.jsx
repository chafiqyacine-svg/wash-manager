import { createContext, useContext, useEffect, useState } from "react";
import { api } from "../api/client.js";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem("token"));
  const [user, setUser] = useState(null);

  // Charge le profil (rôle + site) tant qu'un token est présent.
  useEffect(() => {
    if (!token) { setUser(null); return; }
    api.me().then(setUser).catch(() => setUser(null));
  }, [token]);

  const login = async (email, password) => {
    await api.login(email, password);
    setToken(localStorage.getItem("token"));
  };
  const logout = () => {
    api.logout();
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ token, user, isAuth: !!token, isAdmin: user?.role === "admin", login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
