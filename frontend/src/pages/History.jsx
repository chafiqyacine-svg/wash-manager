import { useEffect, useState } from "react";
import { api } from "../api/client.js";

// Historique : liste des transactions (câblée). Filtres avancés à enrichir.
export default function History() {
  const [txns, setTxns] = useState([]);

  useEffect(() => {
    api.transactions("?limit=100").then(setTxns).catch(() => setTxns([]));
  }, []);

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Historique</h1>
      {/* TODO(dev): barre de filtres (plaque, date, employé, conforme). */}
      <div className="bg-white rounded-lg shadow overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-slate-100 text-left">
            <tr>
              <th className="p-2">#</th>
              <th className="p-2">Détecté</th>
              <th className="p-2">Durée</th>
              <th className="p-2">Conforme</th>
              <th className="p-2">Statut</th>
            </tr>
          </thead>
          <tbody>
            {txns.map((t) => (
              <tr key={t.id} className="border-t">
                <td className="p-2">{t.id}</td>
                <td className="p-2">{t.forfait_detecte ?? "—"}</td>
                <td className="p-2">{t.duree_totale ? `${Math.round(t.duree_totale / 60)} min` : "—"}</td>
                <td className="p-2">
                  {t.conforme === null ? "—" : t.conforme ? "✅" : "❌"}
                </td>
                <td className="p-2">{t.statut}</td>
              </tr>
            ))}
            {txns.length === 0 && (
              <tr><td className="p-3 text-slate-500" colSpan={5}>Aucune transaction.</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
