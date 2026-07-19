import { useEffect, useState } from "react";
import { api } from "../api/client.js";

// Rapprochement manuel : associer un ticket ouvert à une transaction non appariée
// (cas ambigus que l'auto-rapprochement n'a pas résolus).
export default function Rapprochement() {
  const [tickets, setTickets] = useState([]);
  const [transactions, setTransactions] = useState([]);
  const [ticketSel, setTicketSel] = useState(null);
  const [message, setMessage] = useState("");

  const rafraichir = () => {
    api.tickets("ouvert").then(setTickets).catch(() => {});
    api.transactionsNonAppariees().then(setTransactions).catch(() => {});
  };
  useEffect(rafraichir, []);

  const associer = async (txnId) => {
    if (!ticketSel) return;
    setMessage("");
    try {
      await api.rapprocherTicket(ticketSel, txnId);
      setMessage("Rapprochement effectué.");
      setTicketSel(null);
      rafraichir();
    } catch {
      setMessage("Erreur lors du rapprochement.");
    }
  };

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Rapprochement manuel</h1>
      {message && <div className="mb-3 text-sm text-green-700">{message}</div>}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Tickets ouverts — sélectionner celui à associer */}
        <div className="bg-white rounded-lg shadow p-4">
          <h2 className="font-semibold mb-2">Tickets ouverts</h2>
          {tickets.length === 0 && <div className="text-slate-500">Aucun.</div>}
          {tickets.map((t) => (
            <button
              key={t.id}
              onClick={() => setTicketSel(t.id)}
              className={`w-full text-left px-3 py-2 rounded mb-1 border ${
                ticketSel === t.id ? "border-slate-900 bg-slate-100" : "border-slate-200"
              }`}
            >
              #{t.id} — {t.prix} MAD {t.plaque ? `— ${t.plaque}` : ""}
            </button>
          ))}
        </div>

        {/* Transactions non appariées — cliquer pour associer le ticket choisi */}
        <div className="bg-white rounded-lg shadow p-4">
          <h2 className="font-semibold mb-2">Véhicules sans ticket</h2>
          {!ticketSel && (
            <div className="text-slate-400 text-sm mb-2">
              Sélectionnez d'abord un ticket à gauche.
            </div>
          )}
          {transactions.length === 0 && <div className="text-slate-500">Aucun.</div>}
          {transactions.map((tx) => (
            <button
              key={tx.id}
              disabled={!ticketSel}
              onClick={() => associer(tx.id)}
              className="w-full text-left px-3 py-2 rounded mb-1 border border-slate-200 disabled:opacity-40"
            >
              Transaction #{tx.id} — {tx.forfait_detecte ?? "?"} — {tx.duree_totale ?? "?"}s
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
