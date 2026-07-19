import { NavLink } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";

const LINKS = [
  { to: "/", label: "Tableau de bord" },
  { to: "/caisse", label: "Caisse" },
  { to: "/live", label: "Temps réel" },
  { to: "/history", label: "Historique" },
  { to: "/anomalies", label: "Anomalies" },
  { to: "/rapprochement", label: "Rapprochement" },
  { to: "/employees", label: "Employés" },
  { to: "/reports", label: "Rapports" },
  { to: "/config", label: "Configuration" },
];

export default function Sidebar() {
  const { logout } = useAuth();
  return (
    <aside className="w-60 bg-slate-900 text-slate-100 flex flex-col">
      <div className="p-4 text-lg font-bold border-b border-slate-700">
        Wash Manager
      </div>
      <nav className="flex-1 p-2 space-y-1">
        {LINKS.map((l) => (
          <NavLink
            key={l.to}
            to={l.to}
            end={l.to === "/"}
            className={({ isActive }) =>
              `block px-3 py-2 rounded ${
                isActive ? "bg-slate-700" : "hover:bg-slate-800"
              }`
            }
          >
            {l.label}
          </NavLink>
        ))}
      </nav>
      <button
        onClick={logout}
        className="m-2 px-3 py-2 rounded bg-slate-700 hover:bg-slate-600 text-sm"
      >
        Déconnexion
      </button>
    </aside>
  );
}
