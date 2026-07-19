import { useEffect, useState } from "react";
import { api } from "../api/client.js";

const ZONES = [
  { code: "B", label: "Lavage ext." },
  { code: "C", label: "Aspiration" },
  { code: "D", label: "Polish/Cire" },
];

// Configuration : paramètres réglables (fenêtre de rapprochement) + forfaits.
export default function Config() {
  const [fenetre, setFenetre] = useState("");
  const [forfaits, setForfaits] = useState([]);
  const [message, setMessage] = useState("");

  const charger = () => {
    api.parametres().then((p) => setFenetre(p.fenetre_rapprochement_minutes ?? "30")).catch(() => {});
    api.forfaits().then(setForfaits).catch(() => {});
  };
  useEffect(charger, []);

  const enregistrerFenetre = async () => {
    setMessage("");
    try {
      await api.modifierParametre("fenetre_rapprochement_minutes", String(fenetre));
      setMessage("Fenêtre enregistrée.");
    } catch {
      setMessage("Erreur.");
    }
  };

  // Met à jour un champ d'un forfait dans l'état local.
  const majChamp = (id, champ, valeur) =>
    setForfaits((fs) => fs.map((f) => (f.id === id ? { ...f, [champ]: valeur } : f)));

  const toggleZone = (id, code) =>
    setForfaits((fs) =>
      fs.map((f) => {
        if (f.id !== id) return f;
        const zones = f.zones_requises.includes(code)
          ? f.zones_requises.filter((z) => z !== code)
          : [...f.zones_requises, code];
        return { ...f, zones_requises: zones };
      })
    );

  const enregistrerForfait = async (f) => {
    setMessage("");
    try {
      await api.modifierForfait(f.id, {
        prix: Number(f.prix),
        zones_requises: f.zones_requises,
        temps_min: Number(f.temps_min),
        temps_max: Number(f.temps_max),
      });
      setMessage(`Forfait ${f.nom} enregistré.`);
    } catch {
      setMessage("Erreur lors de l'enregistrement du forfait.");
    }
  };

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Configuration</h1>
      {message && <div className="mb-3 text-sm text-green-700">{message}</div>}

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
          <button onClick={enregistrerFenetre} className="bg-slate-900 text-white px-4 py-2 rounded">
            Enregistrer
          </button>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow p-4">
        <h2 className="font-semibold mb-3">Forfaits</h2>
        <div className="space-y-4">
          {forfaits.map((f) => (
            <div key={f.id} className="border rounded p-3">
              <div className="flex items-center justify-between mb-2">
                <span className="font-medium">{f.nom}</span>
                <button
                  onClick={() => enregistrerForfait(f)}
                  className="text-sm bg-slate-900 text-white px-3 py-1 rounded"
                >
                  Enregistrer
                </button>
              </div>
              <div className="grid grid-cols-3 gap-3 text-sm">
                <label className="flex flex-col">
                  Prix (MAD)
                  <input
                    type="number"
                    className="border rounded px-2 py-1"
                    value={f.prix}
                    onChange={(e) => majChamp(f.id, "prix", e.target.value)}
                  />
                </label>
                <label className="flex flex-col">
                  Temps min (min)
                  <input
                    type="number"
                    className="border rounded px-2 py-1"
                    value={f.temps_min}
                    onChange={(e) => majChamp(f.id, "temps_min", e.target.value)}
                  />
                </label>
                <label className="flex flex-col">
                  Temps max (min)
                  <input
                    type="number"
                    className="border rounded px-2 py-1"
                    value={f.temps_max}
                    onChange={(e) => majChamp(f.id, "temps_max", e.target.value)}
                  />
                </label>
              </div>
              <div className="mt-2 flex gap-3 text-sm">
                {ZONES.map((z) => (
                  <label key={z.code} className="flex items-center gap-1">
                    <input
                      type="checkbox"
                      checked={f.zones_requises.includes(z.code)}
                      onChange={() => toggleZone(f.id, z.code)}
                    />
                    {z.label}
                  </label>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
