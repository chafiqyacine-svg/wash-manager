import { useEffect, useState } from "react";
import { api } from "../api/client.js";

// Présence / ponctualité / productivité des employés pour un jour donné.
const BADGE_STATUT = {
  present: "bg-emerald-100 text-emerald-700",
  absent: "bg-red-100 text-red-700",
  non_planifie: "bg-slate-100 text-slate-600",
};
const LIBELLE = { present: "Présent", absent: "Absent", non_planifie: "Non planifié" };

const heure = (iso) => (iso ? new Date(iso).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) : "—");

export default function Presence() {
  const [sites, setSites] = useState([]);
  const [siteId, setSiteId] = useState("");
  const [jour, setJour] = useState(() => new Date().toISOString().slice(0, 10));
  const [lignes, setLignes] = useState([]);

  useEffect(() => { api.sites().then(setSites).catch(() => {}); }, []);
  useEffect(() => {
    api.presence(jour, siteId || undefined).then(setLignes).catch(() => setLignes([]));
  }, [jour, siteId]);

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-bold text-slate-800">Présence & ponctualité</h1>
        <div className="flex gap-2">
          <input type="date" value={jour} onChange={(e) => setJour(e.target.value)}
            className="border rounded-lg px-3 py-2 bg-white text-sm" />
          <select value={siteId} onChange={(e) => setSiteId(e.target.value)}
            className="border rounded-lg px-3 py-2 bg-white text-sm">
            <option value="">Tous les sites</option>
            {sites.map((s) => <option key={s.id} value={s.id}>{s.nom}</option>)}
          </select>
        </div>
      </div>

      <div className="bg-white rounded-2xl shadow-sm overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="text-slate-400 text-left">
            <tr>
              <th className="p-3 font-medium">Employé</th>
              <th className="p-3 font-medium">Statut</th>
              <th className="p-3 font-medium">Prévu</th>
              <th className="p-3 font-medium">Arrivée</th>
              <th className="p-3 font-medium">Départ</th>
              <th className="p-3 font-medium text-right">Retard</th>
              <th className="p-3 font-medium text-right">Présent</th>
              <th className="p-3 font-medium text-right">Actif</th>
              <th className="p-3 font-medium text-right">Temps mort</th>
              <th className="p-3 font-medium text-right">Productivité</th>
            </tr>
          </thead>
          <tbody>
            {lignes.map((l) => (
              <tr key={l.employe_id} className="border-t border-slate-100">
                <td className="p-3 font-medium text-slate-700">{l.nom}</td>
                <td className="p-3">
                  <span className={`text-xs px-2 py-0.5 rounded ${BADGE_STATUT[l.statut] ?? ""}`}>
                    {LIBELLE[l.statut] ?? l.statut}
                  </span>
                </td>
                <td className="p-3 text-slate-600">{l.creneau ?? "—"}</td>
                <td className="p-3 text-slate-600">{heure(l.arrivee)}</td>
                <td className="p-3 text-slate-600">{heure(l.depart)}</td>
                <td className="p-3 text-right">
                  {l.retard_min == null ? "—" : l.retard_min > 0
                    ? <span className="text-amber-600">+{l.retard_min} min</span>
                    : <span className="text-emerald-600">à l'heure</span>}
                </td>
                <td className="p-3 text-right">{l.temps_present_min != null ? `${l.temps_present_min} min` : "—"}</td>
                <td className="p-3 text-right">{l.temps_actif_min} min</td>
                <td className="p-3 text-right">{l.temps_mort_min != null ? `${l.temps_mort_min} min` : "—"}</td>
                <td className="p-3 text-right font-semibold text-slate-800">
                  {l.productivite_pct != null ? `${l.productivite_pct} %` : "—"}
                </td>
              </tr>
            ))}
            {lignes.length === 0 && (
              <tr><td className="p-3 text-slate-400" colSpan={10}>Aucun employé.</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
