import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client.js";
import { useLive } from "../context/LiveContext.jsx";

// Panneau « Transactions » du dashboard : paiements récents (Paid / Pending).
const BADGE = {
  paid: "bg-emerald-100 text-emerald-700",
  pending: "bg-amber-100 text-amber-700",
};

export default function TransactionsCard({ siteId }) {
  const { version } = useLive();
  const [items, setItems] = useState([]);

  useEffect(() => {
    api.payments(siteId).then((d) => setItems(d.items.slice(0, 5))).catch(() => setItems([]));
  }, [siteId, version]);

  return (
    <div className="bg-white rounded-2xl shadow-sm p-5">
      <div className="flex items-center justify-between mb-4">
        <h2 className="font-semibold text-slate-800">Transactions</h2>
        <Link to="/payments" className="text-sm text-blue-600">View all</Link>
      </div>
      <div className="space-y-2">
        {items.map((t) => (
          <div key={t.transaction_id} className="flex items-center justify-between text-sm border-t border-slate-100 pt-2">
            <span className="font-medium text-slate-700">{t.vehicule}</span>
            <span className="text-slate-600">$ {t.montant.toFixed(2)}</span>
            <span className={`text-xs px-2 py-0.5 rounded ${BADGE[t.statut]}`}>
              {t.statut === "paid" ? "Paid" : "Pending"}
            </span>
          </div>
        ))}
        {items.length === 0 && <div className="text-slate-400 text-sm">Aucune transaction.</div>}
      </div>
    </div>
  );
}
