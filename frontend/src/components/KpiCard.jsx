// Carte KPI réutilisable (dashboard).
export default function KpiCard({ label, value, suffix = "" }) {
  return (
    <div className="bg-white rounded-lg shadow p-4">
      <div className="text-sm text-slate-500">{label}</div>
      <div className="text-2xl font-bold mt-1">
        {value}
        {suffix}
      </div>
    </div>
  );
}
