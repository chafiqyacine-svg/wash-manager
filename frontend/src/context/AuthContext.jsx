import { createContext, useContext, useState } from "react";
import { api } from "../api/client.js";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem("token"));

  const login = async (email, password) => {
    await api.login(email, password);
    setToken(localStorage.getItem("token"));
  };
  const logout = () => {
    api.logout();
    setToken(null);
  };

  return (
    <AuthContext.Provider value={{ token, isAuth: !!token, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
