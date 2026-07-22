import { useEffect, useState } from "react";
import { api } from "../api/client.js";
import { useI18n } from "../context/I18nContext.jsx";
import { useLive } from "../context/LiveContext.jsx";

const aujourdhui = () => new Date().toISOString().slice(0, 10);

// Objectifs de pilotage : cibles configurables + écart du jour (atteint / manqué).
export default function Objectifs() {
  const { t } = useI18n();
  const { version } = useLive();
  const [sites, setSites] = useState([]);
  const [siteId, setSiteId] = useState("");
  const [jour, setJour] = useState(aujourdhui());
  const [metriques, setMetriques] = useState([]);
  const [evaluation, setEvaluation] = useState([]);
  const [nouveau, setNouveau] = useState({ metrique: "", cible: "" });

  useEffect(() => {
    api.sites().then(setSites).catch(() => {});
    api.objectifsMetriques().then(setMetriques).catch(() => setMetriques([]));
  }, []);

  const charger = () =>
    api.objectifsEvaluation(jour, siteId || undefined).then(setEvaluation).catch(() => setEvaluation([]));
  useEffect(() => { charger(); }, [jour, siteId, version]);

  const ajouter = async () => {
    if (!nouveau.metrique || nouveau.cible === "") return;
    await api.creerObjectif({
      metrique: nouveau.metrique, cible: Number(nouveau.cible),
      site_id: siteId ? Number(siteId) : null,
    }).catch(() => {});
    setNouveau({ metrique: "", cible: "" });
    charger();
  };
  const retirer = async (id) => { await api.supprimerObjectif(id).catch(() => {}); charger(); };

  const fmt = (v, u) => `${v}${u ? " " + u : ""}`;
  const nonAtteints = evaluation.filter((l) => !l.atteint).length;

  return (
    <div>
      <div className="flex items-center justify-between mb-1">
        <h1 className="text-2xl font-bold text-slate-800">{t("obj.title")}</h1>
        <div className="flex gap-2">
          <input type="date" value={jour} onChange={(e) => setJour(e.target.value)}
            className="border rounded-lg px-3 py-2 bg-white text-sm" />
          <select value={siteId} onChange={(e) => setSiteId(e.target.value)}
            className="border rounded-lg px-3 py-2 bg-white text-sm">
            <option value="">{t("common.all_sites")}</option>
            {sites.map((s) => <option key={s.id} value={s.id}>{s.nom}</option>)}
          </select>
        </div>
      </div>
      <p className="text-sm text-slate-500 mb-4">{t("obj.subtitle")}</p>

      {nonAtteints > 0 && (
        <div className="mb-3 text-sm bg-red-50 text-red-700 rounded-lg px-3 py-2">
          ⚠️ {nonAtteints} {t("obj.missed_warning")}
        </div>
      )}

      <div className="bg-white rounded-2xl shadow-sm overflow-x-auto mb-4">
        <table className="w-full text-sm">
          <thead className="text-slate-400 text-left">
            <tr>
              <th className="p-3 font-medium">{t("obj.metric")}</th>
              <th className="p-3 font-medium">{t("obj.target")}</th>
              <th className="p-3 font-medium text-right">{t("obj.actual")}</th>
              <th className="p-3 font-medium text-right">{t("obj.gap")}</th>
              <th className="p-3 font-medium">{t("obj.status")}</th>
              <th className="p-3 font-medium"></th>
            </tr>
          </thead>
          <tbody>
            {evaluation.map((l) => (
              <tr key={l.id} className={`border-t border-slate-100 ${l.atteint ? "" : "bg-red-50"}`}>
                <td className="p-3 font-medium text-slate-700">{l.label}</td>
                <td className="p-3 text-slate-500">
                  {l.sens === "min" ? "≥ " : "≤ "}{fmt(l.cible, l.unite)}
                </td>
                <td className="p-3 text-right font-semibold text-slate-800">{fmt(l.valeur, l.unite)}</td>
                <td className={`p-3 text-right ${l.ecart >= 0 ? "text-emerald-600" : "text-red-600"}`}>
                  {l.ecart >= 0 ? "+" : ""}{l.ecart}
                </td>
                <td className="p-3">
                  <span className={`inline-flex items-center gap-1.5 text-xs font-medium px-2 py-0.5 rounded-full ${
                    l.atteint ? "bg-emerald-100 text-emerald-700" : "bg-red-100 text-red-700"}`}>
                    <span className={`w-2 h-2 rounded-full ${l.atteint ? "bg-emerald-500" : "bg-red-500"}`} />
                    {l.atteint ? t("obj.ok") : t("obj.ko")}
                  </span>
                </td>
                <td className="p-3 text-right">
                  <button onClick={() => retirer(l.id)} className="text-red-600 text-xs">{t("common.remove")}</button>
                </td>
              </tr>
            ))}
            {evaluation.length === 0 && (
              <tr><td className="p-3 text-slate-400" colSpan={6}>{t("obj.empty")}</td></tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Ajouter un objectif */}
      <div className="bg-white rounded-2xl shadow-sm p-4 max-w-xl">
        <h2 className="font-semibold text-slate-800 mb-2">{t("obj.add")}</h2>
        <div className="flex flex-wrap gap-2 text-sm items-center">
          <select className="border rounded px-2 py-1" value={nouveau.metrique}
            onChange={(e) => setNouveau({ ...nouveau, metrique: e.target.value })}>
            <option value="">{t("obj.metric")}…</option>
            {metriques.map((m) => (
              <option key={m.metrique} value={m.metrique}>
                {m.label} ({m.sens === "min" ? "≥" : "≤"}{m.unite ? " " + m.unite : ""})
              </option>
            ))}
          </select>
          <input type="number" className="border rounded px-2 py-1 w-32" placeholder={t("obj.target")}
            value={nouveau.cible} onChange={(e) => setNouveau({ ...nouveau, cible: e.target.value })} />
          <button onClick={ajouter} disabled={!nouveau.metrique || nouveau.cible === ""}
            className="bg-slate-900 text-white px-4 py-1.5 rounded disabled:opacity-40">
            {t("common.add")}
          </button>
        </div>
      </div>
    </div>
  );
}
