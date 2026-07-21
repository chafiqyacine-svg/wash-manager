import { Fragment, useEffect, useState } from "react";
import { api } from "../api/client.js";

// Marge par forfait : prix de vente − coût des consommables (recette × prix unitaire).
// Le coût dépend des produits du site sélectionné.
export default function Marges() {
  const [sites, setSites] = useState([]);
  const [siteId, setSiteId] = useState("");
  const [marges, setMarges] = useState([]);
  const [ouvert, setOuvert] = useState(null); // forfait_id du détail déplié

  useEffect(() => { api.sites().then(setSites).catch(() => {}); }, []);
  useEffect(() => {
    api.marges(siteId || undefined).then(setMarges).catch(() => setMarges([]));
  }, [siteId]);

  const dh = (v) => `${Number(v).toFixed(2)} DH`;
  const couleurTaux = (t) =>
    t == null ? "text-slate-400"
      : t >= 60 ? "text-emerald-600"
      : t >= 30 ? "text-amber-600"
      : "text-red-600";

  return (
    <div>
      <div className="flex items-center justify-between mb-1">
        <h1 className="text-2xl font-bold text-slate-800">Marge par forfait</h1>
        <select value={siteId} onChange={(e) => setSiteId(e.target.value)}
          className="border rounded-lg px-3 py-2 bg-white text-sm">
          <option value="">Tous les sites</option>
          {sites.map((s) => <option key={s.id} value={s.id}>{s.nom}</option>)}
        </select>
      </div>
      <p className="text-sm text-slate-500 mb-4">
        Coût = somme des consommables par lavage (prix unitaire ÷ lavages par unité).
        Renseignez les prix unitaires dans l'Inventaire et les recettes dans les Réglages.
      </p>

      <div className="bg-white rounded-2xl shadow-sm overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="text-slate-400 text-left">
            <tr>
              <th className="p-3 font-medium">Forfait</th>
              <th className="p-3 font-medium text-right">Prix</th>
              <th className="p-3 font-medium text-right">Coût produits</th>
              <th className="p-3 font-medium text-right">Marge</th>
              <th className="p-3 font-medium text-right">Taux</th>
              <th className="p-3 font-medium"></th>
            </tr>
          </thead>
          <tbody>
            {marges.map((m) => (
              <Fragment key={m.forfait_id}>
                <tr className="border-t border-slate-100">
                  <td className="p-3 font-medium text-slate-700">{m.forfait}</td>
                  <td className="p-3 text-right">{dh(m.prix)}</td>
                  <td className="p-3 text-right text-slate-500">{dh(m.cout_produits)}</td>
                  <td className="p-3 text-right font-semibold text-slate-800">{dh(m.marge)}</td>
                  <td className={`p-3 text-right font-semibold ${couleurTaux(m.taux_marge)}`}>
                    {m.taux_marge == null ? "—" : `${m.taux_marge} %`}
                  </td>
                  <td className="p-3 text-right">
                    {m.detail.length > 0 && (
                      <button className="text-xs text-blue-600"
                        onClick={() => setOuvert(ouvert === m.forfait_id ? null : m.forfait_id)}>
                        {ouvert === m.forfait_id ? "Masquer" : `Détail (${m.detail.length})`}
                      </button>
                    )}
                  </td>
                </tr>
                {ouvert === m.forfait_id && m.detail.map((d) => (
                  <tr key={`${m.forfait_id}-${d.produit_id}`} className="bg-slate-50 text-xs text-slate-500">
                    <td className="p-2 pl-8" colSpan={2}>
                      {d.produit} — {dh(d.prix_unitaire)}/{d.unite}, 1 {d.unite} / {d.lavages_par_unite} lavages
                    </td>
                    <td className="p-2 text-right" colSpan={4}>{dh(d.cout_par_lavage)} / lavage</td>
                  </tr>
                ))}
              </Fragment>
            ))}
            {marges.length === 0 && (
              <tr><td className="p-3 text-slate-400" colSpan={6}>Aucun forfait.</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
