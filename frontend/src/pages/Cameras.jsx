import { useEffect, useState } from "react";
import { api } from "../api/client.js";
import { useI18n } from "../context/I18nContext.jsx";
import { useLive } from "../context/LiveContext.jsx";

// Supervision des caméras : état EN LIGNE / HORS LIGNE + compteurs.
// Une caméra muette = angle mort de surveillance → à repérer vite.
export default function Cameras() {
  const { t } = useI18n();
  const { version } = useLive();
  const [sites, setSites] = useState([]);
  const [siteId, setSiteId] = useState("");
  const [cameras, setCameras] = useState([]);

  useEffect(() => { api.sites().then(setSites).catch(() => {}); }, []);
  const charger = () =>
    api.cameras(siteId || undefined).then(setCameras).catch(() => setCameras([]));
  useEffect(() => { charger(); }, [siteId, version]);

  const nomSite = (id) => sites.find((s) => s.id === id)?.nom ?? "—";
  const silence = (s) =>
    s == null ? "—" : s < 60 ? `${s} s` : `${Math.floor(s / 60)} min`;

  const horsLigne = cameras.filter((c) => !c.en_ligne).length;

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-bold text-slate-800">{t("cam.title")}</h1>
        <select value={siteId} onChange={(e) => setSiteId(e.target.value)}
          className="border rounded-lg px-3 py-2 bg-white text-sm">
          <option value="">{t("common.all_sites")}</option>
          {sites.map((s) => <option key={s.id} value={s.id}>{s.nom}</option>)}
        </select>
      </div>

      {horsLigne > 0 && (
        <div className="mb-3 text-sm bg-red-50 text-red-700 rounded-lg px-3 py-2">
          ⚠️ {horsLigne} {t("cam.offline_warning")}
        </div>
      )}

      <div className="bg-white rounded-2xl shadow-sm overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="text-slate-400 text-left">
            <tr>
              <th className="p-3 font-medium">{t("cam.camera")}</th>
              <th className="p-3 font-medium">{t("common.site")}</th>
              <th className="p-3 font-medium">{t("cam.role")}</th>
              <th className="p-3 font-medium">{t("cam.status")}</th>
              <th className="p-3 font-medium text-right">{t("cam.silence")}</th>
              <th className="p-3 font-medium text-right">Frames</th>
              <th className="p-3 font-medium text-right">Events</th>
              <th className="p-3 font-medium text-right">{t("cam.pending")}</th>
            </tr>
          </thead>
          <tbody>
            {cameras.map((c) => (
              <tr key={c.camera_id} className={`border-t border-slate-100 ${c.en_ligne ? "" : "bg-red-50"}`}>
                <td className="p-3 font-medium text-slate-700">{c.camera_id}</td>
                <td className="p-3 text-slate-500">{nomSite(c.site_id)}</td>
                <td className="p-3 text-slate-500">{c.role ?? "—"}</td>
                <td className="p-3">
                  <span className={`inline-flex items-center gap-1.5 text-xs font-medium px-2 py-0.5 rounded-full ${
                    c.en_ligne ? "bg-emerald-100 text-emerald-700" : "bg-red-100 text-red-700"}`}>
                    <span className={`w-2 h-2 rounded-full ${c.en_ligne ? "bg-emerald-500" : "bg-red-500"}`} />
                    {c.en_ligne ? t("cam.online") : t("cam.offline")}
                  </span>
                </td>
                <td className="p-3 text-right text-slate-500">{silence(c.silence_s)}</td>
                <td className="p-3 text-right text-slate-500">{c.frames_traitees}</td>
                <td className="p-3 text-right text-slate-500">{c.events_envoyes}</td>
                <td className={`p-3 text-right ${c.outbox_en_attente > 0 ? "text-amber-600 font-medium" : "text-slate-500"}`}>
                  {c.outbox_en_attente}
                </td>
              </tr>
            ))}
            {cameras.length === 0 && (
              <tr><td className="p-3 text-slate-400" colSpan={8}>{t("cam.empty")}</td></tr>
            )}
          </tbody>
        </table>
      </div>
      <p className="text-xs text-slate-400 mt-2">{t("cam.hint")}</p>
    </div>
  );
}
