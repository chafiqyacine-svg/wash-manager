// Conteneur de graphique : titre + zone responsive à hauteur fixe.
export default function ChartCard({ title, children }) {
  return (
    <div className="bg-white rounded-lg shadow p-4">
      <h3 className="text-sm font-semibold text-slate-700 mb-3">{title}</h3>
      <div style={{ width: "100%", height: 240 }}>{children}</div>
    </div>
  );
}
