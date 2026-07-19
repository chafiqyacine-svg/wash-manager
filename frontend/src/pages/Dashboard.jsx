import { useEffect, useState } from "react";
import KpiCard from "../components/KpiCard.jsx";
import { api } from "../api/client.js";

// Tableau de bord : KPI du jour + véhicules en cours.
// Le fetch KPI est câblé pour montrer l'intention ; le reste est à compléter.
export default function Dashboard() {
  const [kpi, setKpi] = useState(null);

  useEffect(() => {
    api.kpi().then(setKpi).catch(() => setKpi(null));
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

      <h2 className="text-lg font-semibold mt-8 mb-2">Véhicules en cours</h2>
      {/* TODO(dev): tableau des transactions statut=en_cours (api.enCours()) avec
          zone courante et chronomètre actif. */}
      <div className="bg-white rounded-lg shadow p-4 text-slate-500">
        À câbler : liste temps réel des véhicules sur le site.
      </div>

      {/* TODO(dev): graphique du volume horaire (Recharts) — cf. rapport 9.1. */}
    </div>
  );
}
