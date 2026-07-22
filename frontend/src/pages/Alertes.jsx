import { useEffect, useState } from "react";
import { api } from "../api/client.js";
import { useI18n } from "../context/I18nContext.jsx";
import { useLive } from "../context/LiveContext.jsx";

const STATUT_STYLE = {
  envoye: "bg-emerald-100 text-emerald-700",
  simule: "bg-slate-100 text-slate-500",
  echec: "bg-red-100 text-red-700",
};
const SEV_STYLE = {
  critique: "text-red-600", haute: "text-amber-600",
};

// Alertes : historique des notifications déclenchées + envoi d'un test.
export default function Alertes() {
  const { t } = useI18n();
  const { version } = useLive();
  const [items, setItems] = useState([]);
  const [canaux, setCanaux] = useState(null);
  const [msg, setMsg] = useState("");

  const charger = () => api.notifications().then(setItems).catch(() => setItems([]));
  useEffect(() => {
    charger();
    api.notificationsCanaux().then(setCanaux).catch(() => setCanaux(null));
  }, [version]);

  const tester = async () => {
    setMsg("");
    try { await api.testerNotification(); setMsg(t("alr.test_ok")); charger(); }
    catch { setMsg(t("common.error")); }
  };

  const dt = (s) => new Date(s).toLocaleString();

  return (
    <div>
      <div className="flex items-center justify-between mb-1">
        <h1 className="text-2xl font-bold text-slate-800">{t("alr.title")}</h1>
        <button onClick={tester} className="bg-slate-900 text-white px-4 py-2 rounded text-sm">
          {t("alr.test")}
        </button>
      </div>
      <p className="text-sm text-slate-500 mb-3">{t("alr.subtitle")}</p>

      {canaux && canaux.mode === "simule" && (
        <div className="mb-3 text-sm bg-amber-50 text-amber-800 rounded-lg px-3 py-2">
          ⚙️ {t("alr.simule")}
        </div>
      )}
      {canaux && canaux.mode === "reel" && (
        <div className="mb-3 text-sm bg-emerald-50 text-emerald-700 rounded-lg px-3 py-2">
          ✅ {t("alr.reel")} : {canaux.canaux.join(", ")}
        </div>
      )}
      {msg && <div className="mb-3 text-sm text-blue-700">{msg}</div>}

      <div className="bg-white rounded-2xl shadow-sm overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="text-slate-400 text-left">
            <tr>
              <th className="p-3 font-medium">{t("audit.when")}</th>
              <th className="p-3 font-medium">{t("alr.subject")}</th>
              <th className="p-3 font-medium">{t("alr.channel")}</th>
              <th className="p-3 font-medium">{t("obj.status")}</th>
            </tr>
          </thead>
          <tbody>
            {items.map((n) => (
              <tr key={n.id} className="border-t border-slate-100">
                <td className="p-3 text-slate-500 whitespace-nowrap">{dt(n.cree_at)}</td>
                <td className="p-3">
                  <span className={`font-medium ${SEV_STYLE[n.severite] ?? "text-slate-700"}`}>
                    {n.sujet}
                  </span>
                  <div className="text-xs text-slate-400">{n.message}</div>
                </td>
                <td className="p-3 text-slate-500">
                  {n.canal}{n.destinataire ? ` → ${n.destinataire}` : ""}
                </td>
                <td className="p-3">
                  <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${STATUT_STYLE[n.statut] ?? ""}`}>
                    {t(`alr.statut.${n.statut}`)}
                  </span>
                </td>
              </tr>
            ))}
            {items.length === 0 && (
              <tr><td className="p-3 text-slate-400" colSpan={4}>{t("alr.empty")}</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
