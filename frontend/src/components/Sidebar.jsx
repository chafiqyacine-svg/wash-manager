import { NavLink } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";

// Menu principal (aligné sur la maquette « Clean It »). Les entrées pointent
// vers les pages existantes ; certaines restent des squelettes (TODO(dev)).
const MENU = [
  { to: "/", label: "Home", icon: "🏠" },
  { to: "/queue", label: "Queue Management", icon: "🚗" },
  { to: "/vehicules", label: "Customer Management", icon: "👥" },
  { to: "/bays", label: "Bay Management", icon: "🅿️" },
  { to: "/employees", label: "Employés", icon: "🧑‍🔧" },
  { to: "/pointage", label: "Pointage", icon: "📸" },
  { to: "/payments", label: "Payments", icon: "💲" },
  { to: "/anomalies", label: "Anomalies", icon: "⚠️" },
  { to: "/history", label: "Historique", icon: "🧾" },
  { to: "/reports", label: "Rapports", icon: "📊" },
];

// Réservé aux administrateurs.
const ADMIN = [
  { to: "/users", label: "Utilisateurs", icon: "🔑" },
];

const SUPPORT = [
  { to: "/config", label: "Settings", icon: "⚙️" },
];

function Item({ to, label, icon }) {
  return (
    <NavLink
      to={to}
      end={to === "/"}
      className={({ isActive }) =>
        `flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm ${
          isActive ? "bg-blue-50 text-blue-600 font-medium" : "text-slate-500 hover:bg-slate-50"
        }`
      }
    >
      <span>{icon}</span>
      {label}
    </NavLink>
  );
}

export default function Sidebar() {
  const { logout, isAdmin } = useAuth();
  return (
    <aside className="w-64 bg-white border-r border-slate-100 flex flex-col p-4">
      <div className="flex items-center gap-2 px-2 mb-6">
        <span className="text-2xl">💧</span>
        <span className="text-xl font-bold text-slate-800">Wash Manager</span>
      </div>

      <div className="text-xs text-slate-400 px-3 mb-1">Menu</div>
      <nav className="space-y-1">
        {MENU.map((m) => <Item key={m.to} {...m} />)}
        {isAdmin && ADMIN.map((m) => <Item key={m.to} {...m} />)}
      </nav>

      <div className="text-xs text-slate-400 px-3 mt-6 mb-1">Support</div>
      <nav className="space-y-1">
        {SUPPORT.map((m) => <Item key={m.to} {...m} />)}
      </nav>

      <button
        onClick={logout}
        className="mt-auto flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm text-slate-500 hover:bg-slate-50"
      >
        <span>🚪</span> Déconnexion
      </button>
    </aside>
  );
}
