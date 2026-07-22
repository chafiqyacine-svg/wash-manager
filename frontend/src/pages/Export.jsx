import { useEffect, useState } from "react";
import { api } from "../api/client.js";
import { useI18n } from "../context/I18nContext.jsx";

const ilya = (n) => new Date(Date.now() - n * 864e5).toISOString().slice(0, 10);

// Export comptable : recettes et clôtures en CSV (Excel FR) sur une période.
export default function Export() {
  const { t } = useI18n();
  const [sites, setSites] = useState([]);
  const [siteId, setSiteId] = useState("");
  const [debut, setDebut] = useState(ilya(30));
  const [fin, setFin] = useState(ilya(0));
  const [msg, setMsg] = useState("");

  useEffect(() => { api.sites().then(setSites).catch(() => {}); }, []);

  const exporter = async (type) => {
    setMsg("");
    try {
      await api.exporterCsv(type, { debut, fin, siteId: siteId || undefined });
    } catch { setMsg(t("common.error")); }
  };

  const Carte = ({ type, titre, desc }) => (
    <div className="bg-white rounded-2xl shadow-sm p-5">
      <h2 className="font-semibold text-slate-800">{titre}</h2>
      <p className="text-sm text-slate-500 mt-1 mb-4">{desc}</p>
      <button onClick={() => exporter(type)}
        className="bg-slate-900 text-white px-4 py-2 rounded text-sm">
        ⬇ {t("exp.download")}
      </button>
    </div>
  );

  return (
    <div>
      <h1 className="text-2xl font-bold text-slate-800 mb-1">{t("exp.title")}</h1>
      <p className="text-sm text-slate-500 mb-4">{t("exp.subtitle")}</p>

      <div className="bg-white rounded-2xl shadow-sm p-4 mb-4 flex flex-wrap gap-3 items-end">
        <label className="text-sm">
          <span className="block text-slate-500 mb-1">{t("exp.from")}</span>
          <input type="date" value={debut} onChange={(e) => setDebut(e.target.value)}
            className="border rounded px-3 py-2" />
        </label>
        <label className="text-sm">
          <span className="block text-slate-500 mb-1">{t("exp.to")}</span>
          <input type="date" value={fin} onChange={(e) => setFin(e.target.value)}
            className="border rounded px-3 py-2" />
        </label>
        <label className="text-sm">
          <span className="block text-slate-500 mb-1">{t("common.site")}</span>
          <select value={siteId} onChange={(e) => setSiteId(e.target.value)}
            className="border rounded px-3 py-2 bg-white">
            <option value="">{t("common.all_sites")}</option>
            {sites.map((s) => <option key={s.id} value={s.id}>{s.nom}</option>)}
          </select>
        </label>
      </div>

      {msg && <div className="mb-3 text-sm text-red-600">{msg}</div>}

      <div className="grid md:grid-cols-2 gap-4 max-w-3xl">
        <Carte type="recettes" titre={t("exp.recettes")} desc={t("exp.recettes_desc")} />
        <Carte type="clotures" titre={t("exp.clotures")} desc={t("exp.clotures_desc")} />
      </div>
    </div>
  );
}
