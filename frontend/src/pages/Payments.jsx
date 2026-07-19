import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client.js";

const BADGE = {
  paid: "bg-emerald-100 text-emerald-700",
  pending: "bg-amber-100 text-amber-700",
};

// Page Payments : vue financière (encaissé vs en attente) par site.
export default function Payments() {
  const [sites, setSites] = useState([]);
  const [siteId, setSiteId] = useState("");
  const [data, setData] = useState({ items: [], total_paid: 0, total_pending: 0 });

  useEffect(() => { api.sites().then(setSites).catch(() => {}); }, []);
  useEffect(() => {
    api.payments(siteId || undefined).then(setData).catch(() => setData({ items: [], total_paid: 0, total_pending: 0 }));
  }, [siteId]);

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-bold text-slate-800">Payments</h1>
        <div className="flex gap-2">
          <select value={siteId} onChange={(e) => setSiteId(e.target.value)}
            className="border rounded-lg px-3 py-2 bg-white text-sm">
            <option value="">Tous les sites</option>
            {sites.map((s) => <option key={s.id} value={s.id}>{s.nom}</option>)}
          </select>
          <Link to="/caisse" className="bg-slate-900 text-white px-4 py-2 rounded-lg text-sm">
            Encaisser
          </Link>
        </div>
      </div>

      {/* Totaux */}
      <div className="grid grid-cols-2 gap-4 mb-4 max-w-lg">
        <div className="bg-white rounded-2xl shadow-sm p-4">
          <div className="text-slate-500 text-sm">Encaissé</div>
          <div className="text-2xl font-bold text-emerald-600">$ {data.total_paid.toFixed(2)}</div>
        </div>
        <div className="bg-white rounded-2xl shadow-sm p-4">
          <div className="text-slate-500 text-sm">En attente</div>
          <div className="text-2xl font-bold text-amber-600">$ {data.total_pending.toFixed(2)}</div>
        </div>
      </div>

      {/* Liste */}
      <div className="bg-white rounded-2xl shadow-sm overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="text-slate-400 text-left">
            <tr>
              <th className="p-3 font-medium">Véhicule</th>
              <th className="p-3 font-medium text-right">Montant</th>
              <th className="p-3 font-medium">Statut</th>
              <th className="p-3 font-medium">Heure</th>
            </tr>
          </thead>
          <tbody>
            {data.items.map((t) => (
              <tr key={t.transaction_id} className="border-t border-slate-100">
                <td className="p-3 font-medium text-slate-700">{t.vehicule}</td>
                <td className="p-3 text-right text-slate-700">$ {t.montant.toFixed(2)}</td>
                <td className="p-3">
                  <span className={`text-xs px-2 py-0.5 rounded ${BADGE[t.statut]}`}>
                    {t.statut === "paid" ? "Paid" : "Pending"}
                  </span>
                </td>
                <td className="p-3 text-slate-500">
                  {t.heure ? new Date(t.heure).toLocaleString() : "—"}
                </td>
              </tr>
            ))}
            {data.items.length === 0 && (
              <tr><td className="p-3 text-slate-400" colSpan={4}>Aucune transaction.</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
