import { useEffect, useState } from "react";
import DashboardCharts from "../components/DashboardCharts.jsx";
import KpiCard from "../components/KpiCard.jsx";
import { api } from "../api/client.js";

// Tableau de bord : KPI du jour + véhicules en cours.
// Le fetch KPI est câblé pour montrer l'intention ; le reste est à compléter.
export default function Dashboard() {
  const [kpi, setKpi] = useState(null);
  const [enCours, setEnCours] = useState([]);
  const [graphiques, setGraphiques] = useState(null);

  useEffect(() => {
    api.kpi().then(setKpi).catch(() => setKpi(null));
    api.enCours().then(setEnCours).catch(() => setEnCours([]));
    api.graphiques().then(setGraphiques).catch(() => setGraphiques(null));
    // TODO(dev): ouvrir le WebSocket /api/v1/ws/live pour rafraîchir en temps réel.
  }, []);

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Tableau de bord</h1>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <KpiCard label="Véhicules (jour)" value={kpi?.vehicules ?? "—"} />
        <KpiCard label="Chiffre d'affaires" value={kpi?.chiffre_affaires ?? "—"} suffix=" MAD" />
        <KpiCard label="Temps moyen" value={kpi?.temps_moyen_min ?? "—"} suffix=" min" />
        <KpiCard label="Taux conformité" value={kpi?.taux_conformite ?? "—"} suffix=" %" />
      </div>

      <DashboardCharts data={graphiques} />


      <h2 className="text-lg font-semibold mt-8 mb-2">Véhicules en cours</h2>
      <div className="bg-white rounded-lg shadow overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-slate-100 text-left">
            <tr>
              <th className="p-2">Plaque</th>
              <th className="p-2">Zone</th>
              <th className="p-2">Entré à</th>
            </tr>
          </thead>
          <tbody>
            {enCours.map((v) => (
              <tr key={v.transaction_id} className="border-t">
                <td className="p-2">{v.plaque ?? v.track_id}</td>
                <td className="p-2">Zone {v.zone_courante}</td>
                <td className="p-2">
                  {v.heure_entree ? new Date(v.heure_entree).toLocaleTimeString() : "—"}
                </td>
              </tr>
            ))}
            {enCours.length === 0 && (
              <tr><td className="p-3 text-slate-500" colSpan={3}>Aucun véhicule sur le site.</td></tr>
            )}
          </tbody>
        </table>
      </div>

      {/* TODO(dev): graphique du volume horaire (Recharts) — cf. rapport 9.1. */}
    </div>
  );
}
