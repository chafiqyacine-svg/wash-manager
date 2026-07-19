import { useEffect, useState } from "react";
import { api } from "../api/client.js";

// Bay Management : baies de tous les sites, avec état et charge.
export default function Bays() {
  const [sites, setSites] = useState([]);
  const [bays, setBays] = useState([]);

  useEffect(() => {
    api.sites().then(setSites).catch(() => setSites([]));
    api.bays("all").then(setBays).catch(() => setBays([]));
  }, []);

  const nomSite = (id) => sites.find((s) => s.id === id)?.nom ?? `Site ${id}`;

  return (
    <div>
      <h1 className="text-2xl font-bold text-slate-800 mb-4">Bay Management</h1>
      {/* TODO(dev): endpoint PATCH /bays/{id} pour changer statut/staff, + ajout de baies. */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {bays.map((b) => (
          <div key={b.id} className="bg-white rounded-2xl shadow-sm p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="font-semibold text-slate-700">Baie {b.numero}</span>
              <span className={`text-xs px-2 py-0.5 rounded ${
                b.statut === "hors_service" ? "bg-red-100 text-red-700" : "bg-emerald-100 text-emerald-700"
              }`}>
                {b.statut === "hors_service" ? "Hors service" : "Opérationnelle"}
              </span>
            </div>
            <div className="text-sm text-slate-500">{nomSite(b.site_id)}</div>
            <div className="text-sm text-slate-500 mt-2">
              👥 {b.staff} staff · En file : {b.in_queue}
              {b.avg_time_min != null && ` · ⏱ ${b.avg_time_min} min`}
            </div>
          </div>
        ))}
        {bays.length === 0 && <div className="text-slate-400">Aucune baie.</div>}
      </div>
    </div>
  );
}
