import { useEffect, useState } from "react";
import { api } from "../api/client.js";

// Caisse intégrée : l'opérateur crée un ticket à chaque encaissement.
// Remplace un POS externe et fournit le « forfait payé » pour le rapprochement.
const MODES = [
  { val: "espece", label: "Espèces" },
  { val: "carte", label: "Carte" },
  { val: "autre", label: "Autre" },
];

export default function Caisse() {
  const [forfaits, setForfaits] = useState([]);
  const [plaque, setPlaque] = useState("");
  const [mode, setMode] = useState("espece");
  const [message, setMessage] = useState("");
  const [tickets, setTickets] = useState([]);

  const rafraichir = () => api.tickets().then(setTickets).catch(() => {});

  useEffect(() => {
    api.forfaits().then(setForfaits).catch(() => setForfaits([]));
    rafraichir();
  }, []);

  const encaisser = async (forfait) => {
    setMessage("");
    try {
      await api.creerTicket({ forfait_id: forfait.id, plaque: plaque || null, mode_paiement: mode });
      setMessage(`Ticket ${forfait.nom} créé (${MODES.find((m) => m.val === mode).label}).`);
      setPlaque("");
      rafraichir();
    } catch {
      setMessage("Erreur lors de la création du ticket.");
    }
  };

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Caisse</h1>

      <div className="bg-white rounded-lg shadow p-4 max-w-md">
        <label className="text-sm text-slate-500">Plaque (facultatif)</label>
        <input
          className="w-full border rounded px-3 py-2 mb-4 mt-1"
          placeholder="ex: 12345-A-67"
          value={plaque}
          onChange={(e) => setPlaque(e.target.value)}
        />
        <label className="text-sm text-slate-500">Mode de paiement</label>
        <div className="flex gap-2 mb-4 mt-1">
          {MODES.map((m) => (
            <button
              key={m.val}
              onClick={() => setMode(m.val)}
              className={`flex-1 px-3 py-2 rounded text-sm border ${
                mode === m.val ? "bg-blue-50 border-blue-400 text-blue-700 font-medium"
                  : "bg-white text-slate-500"
              }`}
            >
              {m.label}
            </button>
          ))}
        </div>
        <div className="grid grid-cols-1 gap-2">
          {forfaits.map((f) => (
            <button
              key={f.id}
              onClick={() => encaisser(f)}
              className="flex justify-between items-center bg-slate-900 text-white px-4 py-3 rounded"
            >
              <span>{f.nom}</span>
              <span className="font-bold">{f.prix} MAD</span>
            </button>
          ))}
        </div>
        {message && <div className="mt-3 text-sm text-green-700">{message}</div>}
      </div>

      <h2 className="text-lg font-semibold mt-8 mb-2">Tickets du jour</h2>
      {/* TODO(dev): tableau paginé + bouton annuler (api.annulerTicket) +
          badge de statut (ouvert / rapproché / annulé). */}
      <div className="bg-white rounded-lg shadow p-4 text-slate-500">
        {tickets.length === 0 ? "Aucun ticket." : `${tickets.length} ticket(s).`}
      </div>
    </div>
  );
}
