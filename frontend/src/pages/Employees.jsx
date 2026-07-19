import { useEffect, useState } from "react";
import { api } from "../api/client.js";

// Employés : classement de performance sur une période (cf. section 8 du CDC).
export default function Employees() {
  const [jours, setJours] = useState(7);
  const [perf, setPerf] = useState([]);

  useEffect(() => {
    api.employePerformance(jours).then(setPerf).catch(() => setPerf([]));
  }, [jours]);

  const medaille = (i) => ["🥇", "🥈", "🥉"][i] ?? `${i + 1}.`;

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-bold text-slate-800">Employés</h1>
        <select value={jours} onChange={(e) => setJours(Number(e.target.value))}
          className="border rounded-lg px-3 py-2 bg-white text-sm">
          <option value={1}>Aujourd'hui</option>
          <option value={7}>7 jours</option>
          <option value={30}>30 jours</option>
        </select>
      </div>

      <div className="bg-white rounded-2xl shadow-sm overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="text-slate-400 text-left">
            <tr>
              <th className="p-3 font-medium">#</th>
              <th className="p-3 font-medium">Employé</th>
              <th className="p-3 font-medium text-right">Véhicules</th>
              <th className="p-3 font-medium text-right">Temps moyen</th>
              <th className="p-3 font-medium text-right">Conformité</th>
              <th className="p-3 font-medium text-right">Revenus</th>
              <th className="p-3 font-medium text-right">Score</th>
            </tr>
          </thead>
          <tbody>
            {perf.map((p, i) => (
              <tr key={p.employe_id} className="border-t border-slate-100">
                <td className="p-3">{medaille(i)}</td>
                <td className="p-3 font-medium text-slate-700">{p.nom}</td>
                <td className="p-3 text-right">{p.vehicules}</td>
                <td className="p-3 text-right">{p.temps_moyen_min} min</td>
                <td className="p-3 text-right">{p.taux_conformite} %</td>
                <td className="p-3 text-right">{p.revenus} MAD</td>
                <td className="p-3 text-right font-semibold text-slate-800">{p.score_qualite}</td>
              </tr>
            ))}
            {perf.length === 0 && (
              <tr><td className="p-3 text-slate-400" colSpan={7}>Aucune donnée.</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
