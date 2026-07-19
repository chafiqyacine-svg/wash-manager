import { useEffect, useState } from "react";
import { api } from "../api/client.js";

// Bay Management : baies de tous les sites, éditables (état, staff, ajout).
export default function Bays() {
  const [sites, setSites] = useState([]);
  const [bays, setBays] = useState([]);
  const [nouvelle, setNouvelle] = useState({ site_id: "", numero: "", staff: 3 });
  const [message, setMessage] = useState("");

  const charger = () => {
    api.sites().then(setSites).catch(() => setSites([]));
    api.bays("all").then(setBays).catch(() => setBays([]));
  };
  useEffect(charger, []);

  const basculerStatut = async (b) => {
    const statut = b.statut === "hors_service" ? "operationnelle" : "hors_service";
    await api.modifierBay(b.id, { statut }).catch(() => setMessage("Erreur."));
    charger();
  };

  const majStaff = async (b, delta) => {
    await api.modifierBay(b.id, { staff: Math.max(0, b.staff + delta) }).catch(() => {});
    charger();
  };

  const ajouterBaie = async () => {
    setMessage("");
    try {
      await api.creerBay({
        site_id: Number(nouvelle.site_id),
        numero: Number(nouvelle.numero),
        staff: Number(nouvelle.staff),
      });
      setNouvelle({ site_id: "", numero: "", staff: 3 });
      charger();
    } catch {
      setMessage("Erreur lors de l'ajout de la baie.");
    }
  };

  const nomSite = (id) => sites.find((s) => s.id === id)?.nom ?? `Site ${id}`;

  return (
    <div>
      <h1 className="text-2xl font-bold text-slate-800 mb-4">Bay Management</h1>
      {message && <div className="mb-3 text-sm text-red-600">{message}</div>}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {bays.map((b) => (
          <div key={b.id} className="bg-white rounded-2xl shadow-sm p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="font-semibold text-slate-700">Baie {b.numero}</span>
              <button
                onClick={() => basculerStatut(b)}
                className={`text-xs px-2 py-0.5 rounded ${
                  b.statut === "hors_service"
                    ? "bg-red-100 text-red-700"
                    : "bg-emerald-100 text-emerald-700"
                }`}
              >
                {b.statut === "hors_service" ? "Hors service" : "Opérationnelle"}
              </button>
            </div>
            <div className="text-sm text-slate-500">{nomSite(b.site_id)}</div>
            <div className="flex items-center gap-2 mt-3 text-sm">
              <span className="text-slate-500">👥 Staff</span>
              <button onClick={() => majStaff(b, -1)} className="w-6 h-6 rounded bg-slate-100">−</button>
              <span className="w-6 text-center">{b.staff}</span>
              <button onClick={() => majStaff(b, 1)} className="w-6 h-6 rounded bg-slate-100">+</button>
            </div>
          </div>
        ))}
        {bays.length === 0 && <div className="text-slate-400">Aucune baie.</div>}
      </div>

      {/* Ajouter une baie */}
      <div className="bg-white rounded-2xl shadow-sm p-4 mt-4 max-w-xl">
        <h2 className="font-semibold text-slate-800 mb-2">Ajouter une baie</h2>
        <div className="flex flex-wrap gap-2 items-center text-sm">
          <select
            className="border rounded px-2 py-1"
            value={nouvelle.site_id}
            onChange={(e) => setNouvelle({ ...nouvelle, site_id: e.target.value })}
          >
            <option value="">Site…</option>
            {sites.map((s) => <option key={s.id} value={s.id}>{s.nom}</option>)}
          </select>
          <input
            type="number" placeholder="N°" className="border rounded px-2 py-1 w-20"
            value={nouvelle.numero}
            onChange={(e) => setNouvelle({ ...nouvelle, numero: e.target.value })}
          />
          <input
            type="number" placeholder="Staff" className="border rounded px-2 py-1 w-20"
            value={nouvelle.staff}
            onChange={(e) => setNouvelle({ ...nouvelle, staff: e.target.value })}
          />
          <button
            onClick={ajouterBaie}
            disabled={!nouvelle.site_id || !nouvelle.numero}
            className="bg-slate-900 text-white px-4 py-1.5 rounded disabled:opacity-40"
          >
            Ajouter
          </button>
        </div>
      </div>
    </div>
  );
}
