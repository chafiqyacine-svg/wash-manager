import {
  Bar,
  BarChart,
  Cell,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import ChartCard from "./ChartCard.jsx";

// Palette catégorielle validée (colorblind-safe, cf. skill dataviz).
// L'ordre est fixe : Rapide, Premium, Complet.
const COULEURS_FORFAIT = { Rapide: "#2563eb", Premium: "#d97706", Complet: "#059669" };
const INK = "#334155";
const GRID = "#e2e8f0";

// Axes/grille discrets (marks fins, grille récessive).
const axisProps = { stroke: INK, fontSize: 11, tickLine: false };

export default function DashboardCharts({ data }) {
  if (!data) return null;
  const { volume_horaire = [], repartition_forfaits = [], tendance = [] } = data;

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mt-4">
      {/* Volume horaire — série unique (magnitude), pas de légende nécessaire */}
      <ChartCard title="Volume par heure (aujourd'hui)">
        <ResponsiveContainer>
          <BarChart data={volume_horaire} margin={{ top: 8, right: 8, left: -20, bottom: 0 }}>
            <CartesianGrid stroke={GRID} vertical={false} />
            <XAxis dataKey="heure" {...axisProps} />
            <YAxis allowDecimals={false} {...axisProps} />
            <Tooltip />
            <Bar dataKey="vehicules" fill="#2563eb" radius={[4, 4, 0, 0]} maxBarSize={22} />
          </BarChart>
        </ResponsiveContainer>
      </ChartCard>

      {/* Tendance 7 jours — série unique dans le temps (ligne) */}
      <ChartCard title="Tendance véhicules (7 jours)">
        <ResponsiveContainer>
          <LineChart data={tendance} margin={{ top: 8, right: 8, left: -20, bottom: 0 }}>
            <CartesianGrid stroke={GRID} vertical={false} />
            <XAxis dataKey="date" {...axisProps} />
            <YAxis allowDecimals={false} {...axisProps} />
            <Tooltip />
            <Line type="monotone" dataKey="vehicules" stroke="#2563eb" strokeWidth={2} dot={{ r: 3 }} />
          </LineChart>
        </ResponsiveContainer>
      </ChartCard>

      {/* Répartition des forfaits — catégories (identité) : couleur + label d'axe */}
      <ChartCard title="Répartition des forfaits (aujourd'hui)">
        <ResponsiveContainer>
          <BarChart data={repartition_forfaits} margin={{ top: 8, right: 8, left: -20, bottom: 0 }}>
            <CartesianGrid stroke={GRID} vertical={false} />
            <XAxis dataKey="forfait" {...axisProps} />
            <YAxis allowDecimals={false} {...axisProps} />
            <Tooltip />
            <Bar dataKey="valeur" radius={[4, 4, 0, 0]} maxBarSize={48}>
              {repartition_forfaits.map((d) => (
                <Cell key={d.forfait} fill={COULEURS_FORFAIT[d.forfait] ?? "#64748b"} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </ChartCard>

      {/* Chiffre d'affaires 7 jours */}
      <ChartCard title="Chiffre d'affaires (7 jours, MAD)">
        <ResponsiveContainer>
          <BarChart data={tendance} margin={{ top: 8, right: 8, left: -10, bottom: 0 }}>
            <CartesianGrid stroke={GRID} vertical={false} />
            <XAxis dataKey="date" {...axisProps} />
            <YAxis {...axisProps} />
            <Tooltip />
            <Bar dataKey="ca" fill="#059669" radius={[4, 4, 0, 0]} maxBarSize={22} />
          </BarChart>
        </ResponsiveContainer>
      </ChartCard>
    </div>
  );
}
