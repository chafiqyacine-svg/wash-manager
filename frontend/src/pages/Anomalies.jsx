import { useEffect, useState } from "react";
import { api } from "../api/client.js";

const COULEUR = {
  critique: "bg-red-100 text-red-800",
  haute: "bg-orange-100 text-orange-800",
  moyenne: "bg-yellow-100 text-yellow-800",
  basse: "bg-slate-100 text-slate-700",
};

// Anomalies : liste (câblée) + résolution.
export default function Anomalies() {
  const [items, setItems] = useState([]);

  const charger = () => api.anomalies("?resolu=false").then(setItems).catch(() => setItems([]));
  // Ne pas passer `charger` directement : il renvoie une Promise, que React
  // prendrait pour une fonction de nettoyage.
  useEffect(() => { charger(); }, []);

  const resoudre = async (id) => {
    await api.resoudreAnomalie(id);
    charger();
  };

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Anomalies</h1>
      <div className="space-y-2">
        {items.map((a) => (
          <div key={a.id} className="bg-white rounded-lg shadow p-3 flex items-center justify-between">
            <div>
              <span className={`text-xs px-2 py-0.5 rounded ${COULEUR[a.severite] ?? ""}`}>
                {a.severite}
              </span>
              <span className="ml-2 font-medium">{a.type}</span>
              <div className="text-sm text-slate-600">{a.description}</div>
            </div>
            <button onClick={() => resoudre(a.id)} className="text-sm bg-slate-900 text-white px-3 py-1 rounded">
              Résoudre
            </button>
          </div>
        ))}
        {items.length === 0 && (
          <div className="bg-white rounded-lg shadow p-4 text-slate-500">Aucune anomalie ouverte.</div>
        )}
      </div>
    </div>
  );
}
