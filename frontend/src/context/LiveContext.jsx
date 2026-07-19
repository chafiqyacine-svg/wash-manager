import { createContext, useContext, useEffect, useRef, useState } from "react";
import { useAuth } from "./AuthContext.jsx";

// Fournit un compteur `version` incrémenté à chaque message WebSocket serveur.
// Les composants ajoutent `version` à leurs deps d'effet pour se rafraîchir.
const LiveContext = createContext({ version: 0 });

export function LiveProvider({ children }) {
  const { token, isAuth } = useAuth();
  const [version, setVersion] = useState(0);
  const wsRef = useRef(null);

  useEffect(() => {
    if (!isAuth || !token) return;

    let fermeVoulu = false;
    let reconnectTimer = null;

    const connect = () => {
      const proto = window.location.protocol === "https:" ? "wss" : "ws";
      const url = `${proto}://${window.location.host}/api/v1/ws/live?token=${token}`;
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onmessage = () => setVersion((v) => v + 1);
      ws.onclose = () => {
        if (!fermeVoulu) reconnectTimer = setTimeout(connect, 3000); // reconnexion
      };
      ws.onerror = () => ws.close();
    };
    connect();

    return () => {
      fermeVoulu = true;
      clearTimeout(reconnectTimer);
      wsRef.current?.close();
    };
  }, [token, isAuth]);

  return <LiveContext.Provider value={{ version }}>{children}</LiveContext.Provider>;
}

export const useLive = () => useContext(LiveContext);
