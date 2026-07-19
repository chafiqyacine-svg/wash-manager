import { useEffect, useState } from "react";
import { api } from "../api/client.js";

// Panneau « Wash Bay Stations » : onglets Operational / Out of service / All
// + une carte par baie (lavage en cours, file d'attente, temps moyen, staff).
const ONGLETS = [
  { cle: "operational", label: "Operational" },
  { cle: "out_of_service", label: "Out of service" },
  { cle: "all", label: "All" },
];

function BayCard({ bay }) {
  const cw = bay.current_wash;
  const hs = bay.statut === "hors_service";
  return (
    <div className="border border-slate-100 rounded-xl p-4">
      <div className="flex items-center justify-between mb-3">
        <span className="font-semibold text-slate-700">Baie : {bay.numero}</span>
        <span className={`w-2.5 h-2.5 rounded-full ${hs ? "bg-red-400" : "bg-emerald-400"}`} />
      </div>
      <div className="flex justify-between text-sm mb-3">
        <div>
          <div className="font-medium text-slate-700">{cw?.vehicule ?? "—"}</div>
          <div className="text-slate-400 text-xs">🚗 {cw?.categorie ?? "Libre"}</div>
        </div>
        <div className="text-right">
          <div className="font-medium text-slate-700">{bay.in_queue}</div>
          <div className="text-slate-400 text-xs">En file</div>
        </div>
      </div>
      <div className="flex justify-between text-sm border-t border-slate-100 pt-3">
        <div>
          <div className="font-medium text-slate-700">
            {cw?.elapsed_min != null ? `${cw.elapsed_min} min` : bay.avg_time_min != null ? `${bay.avg_time_min} min` : "—"}
          </div>
          <div className="text-slate-400 text-xs">⏱ Temps moyen</div>
        </div>
        <div className="text-right">
          <div className="font-medium text-slate-700">{bay.staff}</div>
          <div className="text-slate-400 text-xs">👥 Staff</div>
        </div>
      </div>
    </div>
  );
}

export default function BayStations({ siteId }) {
  const [onglet, setOnglet] = useState("operational");
  const [bays, setBays] = useState([]);

  useEffect(() => {
    api.bays(onglet, siteId).then(setBays).catch(() => setBays([]));
  }, [onglet, siteId]);

  return (
    <div className="bg-white rounded-2xl shadow-sm p-5">
      <h2 className="font-semibold text-slate-800 mb-3">Wash Bay Stations</h2>
      <div className="flex gap-4 border-b border-slate-100 mb-4 text-sm">
        {ONGLETS.map((o) => (
          <button
            key={o.cle}
            onClick={() => setOnglet(o.cle)}
            className={`pb-2 -mb-px border-b-2 ${
              onglet === o.cle ? "border-blue-500 text-blue-600 font-medium" : "border-transparent text-slate-400"
            }`}
          >
            {o.label}
          </button>
        ))}
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {bays.map((b) => <BayCard key={b.id} bay={b} />)}
        {bays.length === 0 && <div className="text-slate-400 text-sm">Aucune baie.</div>}
      </div>
    </div>
  );
}
