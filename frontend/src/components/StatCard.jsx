// Carte KPI d'en-tête façon « Clean It » : icône, libellé, valeur, delta vs veille.
export default function StatCard({ icon, label, value, deltaPct, accent = "bg-blue-50" }) {
  const positif = deltaPct != null && deltaPct >= 0;
  return (
    <div className="bg-white rounded-2xl shadow-sm p-5">
      <div className="flex items-center gap-3 mb-4">
        <div className={`w-10 h-10 rounded-full grid place-items-center ${accent}`}>
          <span className="text-lg">{icon}</span>
        </div>
        <span className="text-slate-500 font-medium">{label}</span>
      </div>
      <div className="flex items-end justify-between">
        <div className="text-3xl font-bold text-slate-800">{value}</div>
        {deltaPct != null && (
          <div className={`text-xs ${positif ? "text-emerald-600" : "text-red-500"}`}>
            {positif ? "▲" : "▼"} {Math.abs(deltaPct)}%
            <div className="text-slate-400">vs hier</div>
          </div>
        )}
      </div>
    </div>
  );
}
