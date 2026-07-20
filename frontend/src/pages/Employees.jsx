import { useEffect, useState } from "react";
import { api } from "../api/client.js";
import WeekHoursEditor from "../components/WeekHoursEditor.jsx";

// Employés : effectif par site (affectation) + classement de performance.
export default function Employees() {
  const [sites, setSites] = useState([]);
  const [siteId, setSiteId] = useState("");
  const [jours, setJours] = useState(7);
  const [employes, setEmployes] = useState([]);
  const [perf, setPerf] = useState([]);
  // Édition des horaires de travail d'un employé
  const [empHoraire, setEmpHoraire] = useState(null);   // employé sélectionné
  const [horaires, setHoraires] = useState([]);

  useEffect(() => { api.sites().then(setSites).catch(() => {}); }, []);

  const charger = () => {
    const s = siteId || undefined;
    api.employes(s).then(setEmployes).catch(() => setEmployes([]));
    api.employePerformance(jours, s).then(setPerf).catch(() => setPerf([]));
  };
  useEffect(charger, [siteId, jours]);

  const nomSite = (id) => sites.find((s) => s.id === id)?.nom ?? "Non affecté";

  const affecter = async (empId, newSiteId) => {
    await api.modifierEmploye(empId, { site_id: newSiteId ? Number(newSiteId) : null }).catch(() => {});
    charger();
  };

  const changerCouleur = async (empId, couleur) => {
    await api.modifierEmploye(empId, { couleur_gilet: couleur }).catch(() => {});
    charger();
  };

  const ouvrirHoraires = (emp) => {
    setEmpHoraire(emp);
    api.horairesEmploye(emp.id).then(setHoraires).catch(() => setHoraires([]));
  };

  const medaille = (i) => ["🥇", "🥈", "🥉"][i] ?? `${i + 1}.`;

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-bold text-slate-800">Employés</h1>
        <div className="flex gap-2">
          <select value={siteId} onChange={(e) => setSiteId(e.target.value)}
            className="border rounded-lg px-3 py-2 bg-white text-sm">
            <option value="">Tous les sites</option>
            {sites.map((s) => <option key={s.id} value={s.id}>{s.nom}</option>)}
          </select>
          <select value={jours} onChange={(e) => setJours(Number(e.target.value))}
            className="border rounded-lg px-3 py-2 bg-white text-sm">
            <option value={1}>Aujourd'hui</option>
            <option value={7}>7 jours</option>
            <option value={30}>30 jours</option>
          </select>
        </div>
      </div>

      {/* Effectif + affectation au site */}
      <div className="bg-white rounded-2xl shadow-sm overflow-x-auto mb-4">
        <table className="w-full text-sm">
          <thead className="text-slate-400 text-left">
            <tr>
              <th className="p-3 font-medium">Employé</th>
              <th className="p-3 font-medium">Badge</th>
              <th className="p-3 font-medium">Gilet</th>
              <th className="p-3 font-medium">Site d'affectation</th>
              <th className="p-3 font-medium">Actif</th>
              <th className="p-3 font-medium">Horaires</th>
            </tr>
          </thead>
          <tbody>
            {employes.map((e) => (
              <tr key={e.id} className="border-t border-slate-100">
                <td className="p-3 font-medium text-slate-700">{e.nom}</td>
                <td className="p-3 text-slate-500">{e.badge_nfc_id ?? "—"}</td>
                <td className="p-3">
                  <input type="color" value={e.couleur_gilet ?? "#888888"}
                    onChange={(ev) => changerCouleur(e.id, ev.target.value)}
                    title="Couleur de gilet" className="w-8 h-8 rounded cursor-pointer" />
                </td>
                <td className="p-3">
                  <select value={e.site_id ?? ""} onChange={(ev) => affecter(e.id, ev.target.value)}
                    className="border rounded px-2 py-1">
                    <option value="">Non affecté</option>
                    {sites.map((s) => <option key={s.id} value={s.id}>{s.nom}</option>)}
                  </select>
                </td>
                <td className="p-3">
                  <span className={`text-xs px-2 py-0.5 rounded ${e.actif ? "bg-emerald-100 text-emerald-700" : "bg-slate-200 text-slate-600"}`}>
                    {e.actif ? "Actif" : "Inactif"}
                  </span>
                </td>
                <td className="p-3">
                  <button onClick={() => ouvrirHoraires(e)} className="text-sm text-blue-600">
                    Éditer
                  </button>
                </td>
              </tr>
            ))}
            {employes.length === 0 && (
              <tr><td className="p-3 text-slate-400" colSpan={6}>Aucun employé.</td></tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Éditeur d'horaires de travail de l'employé sélectionné */}
      {empHoraire && (
        <div className="bg-white rounded-2xl shadow-sm p-4 mb-4 max-w-xl">
          <div className="flex items-center justify-between mb-3">
            <h2 className="font-semibold text-slate-800">Horaires — {empHoraire.nom}</h2>
            <button onClick={() => setEmpHoraire(null)} className="text-sm text-slate-400">Fermer</button>
          </div>
          <WeekHoursEditor
            key={empHoraire.id}
            initial={horaires}
            champs={["debut", "fin"]}
            defaut={{ a: "08:00", b: "16:00" }}
            onSave={(h) => api.majHorairesEmploye(empHoraire.id, h)}
          />
        </div>
      )}

      {/* Classement de performance */}
      <h2 className="font-semibold text-slate-800 mb-2">Classement</h2>
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
