import { useEffect, useState } from "react";
import { api } from "../api/client.js";

// Configuration : paramètres réglables (fenêtre de rapprochement) + forfaits.
export default function Config() {
  const [params, setParams] = useState({});
  const [fenetre, setFenetre] = useState("");
  const [message, setMessage] = useState("");

  useEffect(() => {
    api.parametres().then((p) => {
      setParams(p);
      setFenetre(p.fenetre_rapprochement_minutes ?? "30");
    }).catch(() => {});
  }, []);

  const enregistrerFenetre = async () => {
    setMessage("");
    try {
      await api.modifierParametre("fenetre_rapprochement_minutes", String(fenetre));
      setMessage("Enregistré.");
    } catch {
      setMessage("Erreur.");
    }
  };

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Configuration</h1>

      <div className="bg-white rounded-lg shadow p-4 max-w-md mb-6">
        <h2 className="font-semibold mb-2">Rapprochement automatique</h2>
        <label className="text-sm text-slate-500">
          Fenêtre de rapprochement ticket ↔ véhicule (minutes)
        </label>
        <div className="flex gap-2 mt-1">
          <input
            type="number"
            min="1"
            className="border rounded px-3 py-2 w-32"
            value={fenetre}
            onChange={(e) => setFenetre(e.target.value)}
          />
          <button
            onClick={enregistrerFenetre}
            className="bg-slate-900 text-white px-4 py-2 rounded"
          >
            Enregistrer
          </button>
        </div>
        {message && <div className="mt-2 text-sm text-green-700">{message}</div>}
      </div>

      {/* TODO(dev): édition des forfaits (prix, zones_requises, temps_min/max)
          via api.forfaits() + endpoints PUT à ajouter côté backend. */}
      <div className="bg-white rounded-lg shadow p-4 text-slate-500">
        À câbler : édition des forfaits.
      </div>
    </div>
  );
}
