import { useEffect, useState } from "react";
import { api } from "../api/client.js";
import { useLive } from "../context/LiveContext.jsx";

// « Recent Events » : basé sur les anomalies récentes (proxy d'événements).
const ICONE = {
  critique: "🔴",
  haute: "🟠",
  moyenne: "🟡",
  basse: "⚪",
};

export default function RecentEvents() {
  const { version } = useLive();
  const [items, setItems] = useState([]);

  // Se rafraîchit à chaque signal temps réel (nouvelle anomalie / alerte).
  useEffect(() => {
    api.anomalies().then((a) => setItems(a.slice(0, 6))).catch(() => setItems([]));
  }, [version]);

  return (
    <div className="bg-white rounded-2xl shadow-sm p-5">
      <h2 className="font-semibold text-slate-800 mb-4">Recent Events</h2>
      <div className="space-y-3">
        {items.map((a) => (
          <div key={a.id} className="flex items-start gap-3">
            <span>{ICONE[a.severite] ?? "•"}</span>
            <div className="flex-1">
              <div className="text-sm font-medium text-slate-700">
                {a.type}
                {a.site && <span className="ml-2 text-xs text-slate-400">· 📍 {a.site}</span>}
              </div>
              <div className="text-xs text-slate-400 line-clamp-1">{a.description}</div>
            </div>
          </div>
        ))}
        {items.length === 0 && <div className="text-slate-400 text-sm">Aucun événement.</div>}
      </div>
    </div>
  );
}
