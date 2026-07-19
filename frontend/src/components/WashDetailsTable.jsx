// Tableau « Wash Details » : véhicule, catégorie, baie, statut, montant.
const BADGE_CAT = "bg-slate-100 text-slate-700";
const BADGE_STATUT = {
  ontime: "bg-emerald-100 text-emerald-700",
  delayed: "bg-amber-100 text-amber-700",
};

export default function WashDetailsTable({ rows = [] }) {
  return (
    <div className="bg-white rounded-2xl shadow-sm p-5">
      <h2 className="font-semibold text-slate-800 mb-4">Wash Details</h2>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="text-slate-400 text-left">
            <tr>
              <th className="pb-2 font-medium">Véhicule</th>
              <th className="pb-2 font-medium">Catégorie</th>
              <th className="pb-2 font-medium">Baie</th>
              <th className="pb-2 font-medium">Statut</th>
              <th className="pb-2 font-medium text-right">Montant</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.transaction_id} className="border-t border-slate-100">
                <td className="py-2 font-medium text-slate-700">{r.vehicule ?? "—"}</td>
                <td className="py-2">
                  <span className={`text-xs px-2 py-0.5 rounded ${BADGE_CAT}`}>{r.categorie ?? "—"}</span>
                </td>
                <td className="py-2 text-slate-600">{r.bay ?? "—"}</td>
                <td className="py-2">
                  <span className={`text-xs px-2 py-0.5 rounded ${BADGE_STATUT[r.statut] ?? ""}`}>
                    {r.statut === "delayed" ? "Delayed" : "Ontime"}
                  </span>
                </td>
                <td className="py-2 text-right text-slate-700">
                  {r.montant != null ? `$ ${r.montant.toFixed(2)}` : "—"}
                </td>
              </tr>
            ))}
            {rows.length === 0 && (
              <tr><td className="py-3 text-slate-400" colSpan={5}>Aucun lavage aujourd'hui.</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
