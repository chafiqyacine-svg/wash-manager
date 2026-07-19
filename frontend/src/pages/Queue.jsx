import { useEffect, useState } from "react";
import { api } from "../api/client.js";
import { useLive } from "../context/LiveContext.jsx";

// Queue Management (mode manuel) : file d'attente des tickets payés + lavages
// en cours. Permet de démarrer un lavage sur une baie et de le terminer —
// exploitation à la main tant que les caméras ne sont pas installées.
export default function Queue() {
  const { version } = useLive();
  const [sites, setSites] = useState([]);
  const [siteId, setSiteId] = useState("");
  const [bays, setBays] = useState([]);
  const [data, setData] = useState({ en_attente: [], en_cours: [] });
  const [selBay, setSelBay] = useState({}); // ticket_id -> bay_id
  const [message, setMessage] = useState("");

  const charger = () => {
    const s = siteId || undefined;
    api.queue(s).then(setData).catch(() => setData({ en_attente: [], en_cours: [] }));
    api.bays("operational", s).then(setBays).catch(() => setBays([]));
  };
  useEffect(charger, [siteId, version]);
  useEffect(() => { api.sites().then(setSites).catch(() => {}); }, []);

  const demarrer = async (ticketId) => {
    const bayId = selBay[ticketId] || bays[0]?.id;
    if (!bayId) return;
    setMessage("");
    try {
      await api.demarrerLavage(ticketId, bayId);
      charger();
    } catch {
      setMessage("Impossible de démarrer (ticket ou baie indisponible).");
    }
  };

  const terminer = async (txnId) => {
    setMessage("");
    try {
      await api.terminerLavage(txnId);
      charger();
    } catch {
      setMessage("Impossible de terminer.");
    }
  };

  const nomBaie = (id) => {
    const b = bays.find((x) => x.id === id);
    return b ? `Baie ${b.numero}` : `Baie #${id}`;
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-bold text-slate-800">Queue Management</h1>
        <select value={siteId} onChange={(e) => setSiteId(e.target.value)}
          className="border rounded-lg px-3 py-2 bg-white text-sm">
          <option value="">Tous les sites</option>
          {sites.map((s) => <option key={s.id} value={s.id}>{s.nom}</option>)}
        </select>
      </div>
      {message && <div className="mb-3 text-sm text-red-600">{message}</div>}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* File d'attente */}
        <div className="bg-white rounded-2xl shadow-sm p-5">
          <h2 className="font-semibold text-slate-800 mb-3">
            En attente ({data.en_attente.length})
          </h2>
          <div className="space-y-2">
            {data.en_attente.map((t) => (
              <div key={t.ticket_id} className="flex items-center gap-2 border border-slate-100 rounded-lg p-2">
                <div className="flex-1 text-sm">
                  <div className="font-medium text-slate-700">{t.plaque ?? "Sans plaque"}</div>
                  <div className="text-slate-400 text-xs">{t.prix} MAD</div>
                </div>
                <select
                  className="border rounded px-2 py-1 text-sm"
                  value={selBay[t.ticket_id] ?? ""}
                  onChange={(e) => setSelBay({ ...selBay, [t.ticket_id]: e.target.value })}
                >
                  <option value="">Baie…</option>
                  {bays.map((b) => <option key={b.id} value={b.id}>Baie {b.numero}</option>)}
                </select>
                <button onClick={() => demarrer(t.ticket_id)}
                  className="bg-blue-600 text-white text-sm px-3 py-1 rounded">
                  Démarrer
                </button>
              </div>
            ))}
            {data.en_attente.length === 0 && <div className="text-slate-400 text-sm">File vide.</div>}
          </div>
        </div>

        {/* Lavages en cours */}
        <div className="bg-white rounded-2xl shadow-sm p-5">
          <h2 className="font-semibold text-slate-800 mb-3">
            En cours ({data.en_cours.length})
          </h2>
          <div className="space-y-2">
            {data.en_cours.map((tx) => (
              <div key={tx.transaction_id} className="flex items-center gap-2 border border-slate-100 rounded-lg p-2">
                <div className="flex-1 text-sm">
                  <div className="font-medium text-slate-700">{tx.plaque}</div>
                  <div className="text-slate-400 text-xs">{nomBaie(tx.bay_id)}</div>
                </div>
                <button onClick={() => terminer(tx.transaction_id)}
                  className="bg-emerald-600 text-white text-sm px-3 py-1 rounded">
                  Terminer
                </button>
              </div>
            ))}
            {data.en_cours.length === 0 && <div className="text-slate-400 text-sm">Aucun lavage en cours.</div>}
          </div>
        </div>
      </div>
    </div>
  );
}
