import { useEffect, useState } from "react";
import BayStations from "../components/BayStations.jsx";
import DashboardCharts from "../components/DashboardCharts.jsx";
import RecentEvents from "../components/RecentEvents.jsx";
import StatCard from "../components/StatCard.jsx";
import TransactionsCard from "../components/TransactionsCard.jsx";
import WashDetailsTable from "../components/WashDetailsTable.jsx";
import { api } from "../api/client.js";

// Tableau de bord multi-sites (style « Clean It »).
export default function Dashboard() {
  const [sites, setSites] = useState([]);
  const [siteId, setSiteId] = useState(""); // "" = tous les sites
  const [apercu, setApercu] = useState(null);
  const [washDetails, setWashDetails] = useState([]);
  const [graphiques, setGraphiques] = useState(null);

  useEffect(() => {
    api.sites().then(setSites).catch(() => setSites([]));
  }, []);

  useEffect(() => {
    const s = siteId || undefined;
    api.apercu(s).then(setApercu).catch(() => setApercu(null));
    api.washDetails(s).then(setWashDetails).catch(() => setWashDetails([]));
    api.graphiques().then(setGraphiques).catch(() => setGraphiques(null));
    // TODO(dev): WebSocket temps réel pour rafraîchir apercu/bays automatiquement.
  }, [siteId]);

  const fmt = (v) => (v == null ? "—" : v);

  return (
    <div>
      {/* En-tête : titre + sélecteur de site (multi-emplacements) */}
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-slate-800">Tableau de bord</h1>
        <select
          value={siteId}
          onChange={(e) => setSiteId(e.target.value)}
          className="border rounded-lg px-3 py-2 bg-white text-sm"
        >
          <option value="">Tous les sites</option>
          {sites.map((s) => (
            <option key={s.id} value={s.id}>{s.nom}</option>
          ))}
        </select>
      </div>

      {/* 4 cartes KPI */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard icon="🚿" label="Ongoing wash" accent="bg-rose-50"
          value={String(apercu?.ongoing.valeur ?? "—").padStart(2, "0")}
          deltaPct={apercu?.ongoing.delta_pct} />
        <StatCard icon="📋" label="In order" accent="bg-blue-50"
          value={String(apercu?.in_order.valeur ?? "—").padStart(2, "0")}
          deltaPct={apercu?.in_order.delta_pct} />
        <StatCard icon="✅" label="Completed wash" accent="bg-emerald-50"
          value={String(apercu?.completed.valeur ?? "—").padStart(2, "0")}
          deltaPct={apercu?.completed.delta_pct} />
        <StatCard icon="💲" label="Revenue" accent="bg-amber-50"
          value={`$ ${fmt(apercu?.revenue.valeur)}`}
          deltaPct={apercu?.revenue.delta_pct} />
      </div>

      {/* Wash Details + Bay Stations */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4 mt-4">
        <WashDetailsTable rows={washDetails} />
        <BayStations siteId={siteId || undefined} />
      </div>

      {/* Transactions + Package Analytics + Recent Events */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4 mt-4">
        <TransactionsCard siteId={siteId || undefined} />
        <div className="xl:col-span-2">
          <DashboardCharts data={graphiques} />
        </div>
      </div>
      <div className="mt-4">
        <RecentEvents />
      </div>
    </div>
  );
}
