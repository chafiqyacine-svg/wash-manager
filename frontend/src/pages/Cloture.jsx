import { useEffect, useState } from "react";
import { api } from "../api/client.js";
import { useI18n } from "../context/I18nContext.jsx";

const MODE_LABEL = { espece: "Espèces", carte: "Carte", autre: "Autre" };
const aujourdhui = () => new Date().toISOString().slice(0, 10);

// Clôture de caisse (rapport Z) : aperçu des encaissements du jour par mode,
// saisie du montant réellement compté, calcul de l'écart, archivage PDF.
export default function Cloture() {
  const { t } = useI18n();
  const [sites, setSites] = useState([]);
  const [siteId, setSiteId] = useState("");
  const [jour, setJour] = useState(aujourdhui());
  const [apercu, setApercu] = useState(null);
  const [fond, setFond] = useState(0);
  const [compte, setCompte] = useState(0);
  const [notes, setNotes] = useState("");
  const [historique, setHistorique] = useState([]);
  const [message, setMessage] = useState("");

  useEffect(() => { api.sites().then(setSites).catch(() => {}); }, []);

  const chargerApercu = () =>
    api.clotureApercu(jour, siteId || undefined).then(setApercu).catch(() => setApercu(null));
  const chargerHistorique = () =>
    api.clotures(siteId || undefined).then(setHistorique).catch(() => setHistorique([]));

  useEffect(() => { chargerApercu(); chargerHistorique(); }, [jour, siteId]);

  const dh = (v) => `${Number(v ?? 0).toFixed(2)} DH`;
  const especes = apercu?.total_especes ?? 0;
  const ecartPrev = Number(compte) - (Number(fond) + Number(especes));

  const cloturer = async () => {
    setMessage("");
    try {
      await api.cloturer({
        jour, site_id: siteId ? Number(siteId) : null,
        montant_compte: Number(compte), fond_caisse: Number(fond),
        notes: notes || null,
      });
      setMessage(t("cloture.done"));
      setCompte(0); setFond(0); setNotes("");
      chargerApercu(); chargerHistorique();
    } catch (e) {
      setMessage(String(e).includes("409") ? t("cloture.already") : t("common.error"));
    }
  };

  const nomSite = (id) => sites.find((s) => s.id === id)?.nom ?? t("common.all_sites");

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-bold text-slate-800">{t("cloture.title")}</h1>
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

      <div className="grid md:grid-cols-2 gap-4">
        {/* Aperçu des encaissements */}
        <div className="bg-white rounded-2xl shadow-sm p-4">
          <h2 className="font-semibold text-slate-800 mb-3">{t("cloture.collected")}</h2>
          <table className="w-full text-sm">
            <tbody>
              {Object.entries(apercu?.detail_modes ?? {}).map(([m, v]) => (
                <tr key={m} className="border-b border-slate-100">
                  <td className="py-2 text-slate-600">{MODE_LABEL[m] ?? m}</td>
                  <td className="py-2 text-right text-slate-400">{v.nb}</td>
                  <td className="py-2 text-right font-medium">{dh(v.total)}</td>
                </tr>
              ))}
              {(!apercu || apercu.nb_tickets === 0) && (
                <tr><td className="py-2 text-slate-400" colSpan={3}>{t("cloture.no_ticket")}</td></tr>
              )}
            </tbody>
            {apercu && apercu.nb_tickets > 0 && (
              <tfoot>
                <tr className="font-semibold text-slate-800">
                  <td className="py-2">{t("marges.price")}</td>
                  <td className="py-2 text-right">{apercu.nb_tickets}</td>
                  <td className="py-2 text-right">{dh(apercu.total_theorique)}</td>
                </tr>
              </tfoot>
            )}
          </table>
        </div>

        {/* Comptage & clôture */}
        <div className="bg-white rounded-2xl shadow-sm p-4">
          <h2 className="font-semibold text-slate-800 mb-3">{t("cloture.count")}</h2>
          {apercu?.deja_cloturee ? (
            <div className="text-sm bg-emerald-50 text-emerald-700 rounded-lg px-3 py-2">
              {t("cloture.already")}
            </div>
          ) : (
            <div className="space-y-3 text-sm">
              <label className="block">
                <span className="text-slate-500">{t("cloture.float")}</span>
                <input type="number" step="0.01" value={fond}
                  onChange={(e) => setFond(e.target.value)}
                  className="w-full border rounded px-3 py-2 mt-1" />
              </label>
              <label className="block">
                <span className="text-slate-500">{t("cloture.counted")}</span>
                <input type="number" step="0.01" value={compte}
                  onChange={(e) => setCompte(e.target.value)}
                  className="w-full border rounded px-3 py-2 mt-1" />
              </label>
              <div className="flex justify-between text-slate-500">
                <span>{t("cloture.expected_cash")}</span>
                <span>{dh(Number(fond) + Number(especes))}</span>
              </div>
              <div className={`flex justify-between font-semibold ${
                ecartPrev === 0 ? "text-emerald-600" : "text-red-600"}`}>
                <span>{t("cloture.gap")}</span>
                <span>{dh(ecartPrev)}</span>
              </div>
              <textarea value={notes} onChange={(e) => setNotes(e.target.value)}
                placeholder={t("cloture.notes")} rows={2}
                className="w-full border rounded px-3 py-2" />
              <button onClick={cloturer}
                className="w-full bg-slate-900 text-white px-4 py-2 rounded">
                {t("cloture.close_btn")}
              </button>
            </div>
          )}
          {message && <div className="mt-3 text-sm text-blue-700">{message}</div>}
        </div>
      </div>

      {/* Historique des clôtures */}
      <h2 className="font-semibold text-slate-800 mt-6 mb-2">{t("cloture.history")}</h2>
      <div className="bg-white rounded-2xl shadow-sm overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="text-slate-400 text-left">
            <tr>
              <th className="p-3 font-medium">{t("cloture.day")}</th>
              <th className="p-3 font-medium">{t("common.site")}</th>
              <th className="p-3 font-medium text-right">{t("marges.price")}</th>
              <th className="p-3 font-medium text-right">{t("cloture.counted")}</th>
              <th className="p-3 font-medium text-right">{t("cloture.gap")}</th>
              <th className="p-3 font-medium"></th>
            </tr>
          </thead>
          <tbody>
            {historique.map((c) => (
              <tr key={c.id} className="border-t border-slate-100">
                <td className="p-3 text-slate-700">{c.jour}</td>
                <td className="p-3 text-slate-500">{nomSite(c.site_id)}</td>
                <td className="p-3 text-right">{dh(c.total_theorique)}</td>
                <td className="p-3 text-right">{dh(c.montant_compte)}</td>
                <td className={`p-3 text-right font-medium ${
                  Number(c.ecart) === 0 ? "text-emerald-600" : "text-red-600"}`}>{dh(c.ecart)}</td>
                <td className="p-3 text-right">
                  {c.fichier_pdf && (
                    <button className="text-blue-600 text-xs"
                      onClick={() => api.telechargerCloturePdf(c.id).catch(() => {})}>PDF</button>
                  )}
                </td>
              </tr>
            ))}
            {historique.length === 0 && (
              <tr><td className="p-3 text-slate-400" colSpan={6}>{t("cloture.no_history")}</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
