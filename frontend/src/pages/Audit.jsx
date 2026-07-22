import { useEffect, useState } from "react";
import { api } from "../api/client.js";
import { useI18n } from "../context/I18nContext.jsx";
import { useLive } from "../context/LiveContext.jsx";

// Libellés lisibles des actions journalisées.
const LABELS = {
  "ticket.annuler": "Annulation ticket",
  "ticket.rapprocher": "Rapprochement manuel",
  "forfait.modifier": "Modification forfait",
  "forfait.supprimer": "Suppression forfait",
  "anomalie.resoudre": "Résolution anomalie",
  "cloture.creer": "Clôture de caisse",
  "stock.mouvement": "Mouvement de stock",
  "produit.supprimer": "Suppression produit",
};

// Journal d'audit : qui a fait quelle action sensible, quand (contrôle interne).
export default function Audit() {
  const { t } = useI18n();
  const { version } = useLive();
  const [entrees, setEntrees] = useState([]);
  const [action, setAction] = useState("");

  const charger = () =>
    api.audit(action || undefined).then(setEntrees).catch(() => setEntrees([]));
  useEffect(() => { charger(); }, [action, version]);

  const dt = (s) => new Date(s).toLocaleString();
  const resume = (e) => {
    const d = e.details || {};
    if (e.action === "cloture.creer") return `écart ${d.ecart} DH, total ${d.total} DH`;
    if (e.action === "stock.mouvement") return `${d.produit}: ${d.delta > 0 ? "+" : ""}${d.delta} → ${d.nouvelle_quantite}`;
    if (e.action === "forfait.modifier") return `${d.ancien_prix} → ${d.nouveau_prix} DH`;
    if (e.action === "ticket.annuler") return `${d.prix} DH (${d.mode_paiement})`;
    return Object.keys(d).length ? JSON.stringify(d) : "—";
  };

  const actions = [...new Set(entrees.map((e) => e.action))];

  return (
    <div>
      <div className="flex items-center justify-between mb-1">
        <h1 className="text-2xl font-bold text-slate-800">{t("audit.title")}</h1>
        <select value={action} onChange={(e) => setAction(e.target.value)}
          className="border rounded-lg px-3 py-2 bg-white text-sm">
          <option value="">{t("audit.all_actions")}</option>
          {Object.keys(LABELS).map((a) => <option key={a} value={a}>{LABELS[a]}</option>)}
        </select>
      </div>
      <p className="text-sm text-slate-500 mb-4">{t("audit.subtitle")}</p>

      <div className="bg-white rounded-2xl shadow-sm overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="text-slate-400 text-left">
            <tr>
              <th className="p-3 font-medium">{t("audit.when")}</th>
              <th className="p-3 font-medium">{t("audit.who")}</th>
              <th className="p-3 font-medium">{t("audit.action")}</th>
              <th className="p-3 font-medium">{t("audit.detail")}</th>
            </tr>
          </thead>
          <tbody>
            {entrees.map((e) => (
              <tr key={e.id} className="border-t border-slate-100">
                <td className="p-3 text-slate-500 whitespace-nowrap">{dt(e.created_at)}</td>
                <td className="p-3">
                  <span className="text-slate-700">{e.utilisateur_email ?? "—"}</span>
                  {e.role && <span className="ml-1 text-xs text-slate-400">({e.role})</span>}
                </td>
                <td className="p-3 font-medium text-slate-700">{LABELS[e.action] ?? e.action}</td>
                <td className="p-3 text-slate-500">{resume(e)}</td>
              </tr>
            ))}
            {entrees.length === 0 && (
              <tr><td className="p-3 text-slate-400" colSpan={4}>{t("audit.empty")}</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
