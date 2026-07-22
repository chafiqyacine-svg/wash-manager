import { NavLink } from "react-router-dom";
import LangSwitcher from "./LangSwitcher.jsx";
import { useAuth } from "../context/AuthContext.jsx";
import { useI18n } from "../context/I18nContext.jsx";

// Menu principal (aligné sur la maquette « Clean It »). `key` = clé de traduction.
const MENU = [
  { to: "/", key: "nav.home", icon: "🏠" },
  { to: "/queue", key: "nav.queue", icon: "🚗" },
  { to: "/vehicules", key: "nav.customers", icon: "👥" },
  { to: "/bays", key: "nav.bays", icon: "🅿️" },
  { to: "/employees", key: "nav.employees", icon: "🧑‍🔧" },
  { to: "/pointage", key: "nav.pointage", icon: "📸" },
  { to: "/presence", key: "nav.presence", icon: "🕒" },
  { to: "/payments", key: "nav.payments", icon: "💲" },
  { to: "/cloture", key: "nav.cloture", icon: "🧮" },
  { to: "/inventory", key: "nav.inventory", icon: "📦" },
  { to: "/marges", key: "nav.marges", icon: "💰" },
  { to: "/cameras", key: "nav.cameras", icon: "📹" },
  { to: "/anomalies", key: "nav.anomalies", icon: "⚠️" },
  { to: "/history", key: "nav.history", icon: "🧾" },
  { to: "/reports", key: "nav.reports", icon: "📊" },
];

// Réservé aux administrateurs.
const ADMIN = [
  { to: "/users", key: "nav.users", icon: "🔑" },
];

const SUPPORT = [
  { to: "/config", key: "nav.settings", icon: "⚙️" },
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
  const { logout, isAdmin, user } = useAuth();
  const { t } = useI18n();
  const estControleur = isAdmin || user?.role === "manager";
  return (
    <aside className="w-64 bg-white border-r border-slate-100 flex flex-col p-4">
      <div className="flex items-center justify-between px-2 mb-6">
        <div className="flex items-center gap-2">
          <span className="text-2xl">💧</span>
          <span className="text-xl font-bold text-slate-800">{t("app.title")}</span>
        </div>
        <LangSwitcher />
      </div>

      <div className="text-xs text-slate-400 px-3 mb-1">{t("nav.menu")}</div>
      <nav className="space-y-1">
        {MENU.map((m) => <Item key={m.to} to={m.to} icon={m.icon} label={t(m.key)} />)}
        {estControleur && <Item to="/audit" icon="📋" label={t("nav.audit")} />}
        {isAdmin && ADMIN.map((m) => <Item key={m.to} to={m.to} icon={m.icon} label={t(m.key)} />)}
      </nav>

      <div className="text-xs text-slate-400 px-3 mt-6 mb-1">{t("nav.support")}</div>
      <nav className="space-y-1">
        {SUPPORT.map((m) => <Item key={m.to} to={m.to} icon={m.icon} label={t(m.key)} />)}
      </nav>

      <button
        onClick={logout}
        className="mt-auto flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm text-slate-500 hover:bg-slate-50"
      >
        <span>🚪</span> {t("nav.logout")}
      </button>
    </aside>
  );
}
