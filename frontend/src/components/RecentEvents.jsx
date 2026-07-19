import { useEffect, useState } from "react";
import { api } from "../api/client.js";

// « Recent Events » : basé sur les anomalies récentes (proxy d'événements).
const ICONE = {
  critique: "🔴",
  haute: "🟠",
  moyenne: "🟡",
  basse: "⚪",
};

export default function RecentEvents() {
  const [items, setItems] = useState([]);

  useEffect(() => {
    api.anomalies().then((a) => setItems(a.slice(0, 6))).catch(() => setItems([]));
  }, []);

  return (
    <div className="bg-white rounded-2xl shadow-sm p-5">
      <h2 className="font-semibold text-slate-800 mb-4">Recent Events</h2>
      <div className="space-y-3">
        {items.map((a) => (
          <div key={a.id} className="flex items-start gap-3">
            <span>{ICONE[a.severite] ?? "•"}</span>
            <div className="flex-1">
              <div className="text-sm font-medium text-slate-700">{a.type}</div>
              <div className="text-xs text-slate-400 line-clamp-1">{a.description}</div>
            </div>
          </div>
        ))}
        {items.length === 0 && <div className="text-slate-400 text-sm">Aucun événement.</div>}
      </div>
    </div>
  );
}
