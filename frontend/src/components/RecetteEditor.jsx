import { useEffect, useState } from "react";
import { api } from "../api/client.js";

// Éditeur de recette : quels produits un forfait consomme et à quel rythme
// (« 1 unité tous les N lavages »).
export default function RecetteEditor() {
  const [forfaits, setForfaits] = useState([]);
  const [produits, setProduits] = useState([]);
  const [forfaitId, setForfaitId] = useState("");
  const [lignes, setLignes] = useState([]);
  const [message, setMessage] = useState("");

  useEffect(() => {
    api.forfaits().then(setForfaits).catch(() => {});
    api.produits().then(setProduits).catch(() => {});
  }, []);

  useEffect(() => {
    if (forfaitId) api.consommation(forfaitId).then(setLignes).catch(() => setLignes([]));
    else setLignes([]);
  }, [forfaitId]);

  const nomProduit = (id) => {
    const p = produits.find((x) => x.id === id);
    return p ? `${p.nom} (${p.unite})` : `#${id}`;
  };

  const ajouterLigne = () =>
    setLignes([...lignes, { produit_id: produits[0]?.id ?? "", lavages_par_unite: 20 }]);
  const majLigne = (i, champ, val) =>
    setLignes(lignes.map((l, j) => (j === i ? { ...l, [champ]: val } : l)));
  const retirer = (i) => setLignes(lignes.filter((_, j) => j !== i));

  const enregistrer = async () => {
    setMessage("");
    try {
      await api.majConsommation(forfaitId, lignes.map((l) => ({
        produit_id: Number(l.produit_id),
        lavages_par_unite: Number(l.lavages_par_unite),
      })));
      setMessage("Recette enregistrée.");
    } catch { setMessage("Erreur."); }
  };

  return (
    <div className="bg-white rounded-2xl shadow-sm p-4 mt-6">
      <div className="flex items-center justify-between mb-3">
        <div>
          <h2 className="font-semibold text-slate-800">Consommation produits par forfait</h2>
          <p className="text-xs text-slate-400">
            Définissez quels produits chaque forfait consomme (1 unité tous les N lavages).
          </p>
        </div>
        <select value={forfaitId} onChange={(e) => setForfaitId(e.target.value)}
          className="border rounded-lg px-3 py-1.5 text-sm">
          <option value="">Choisir un forfait…</option>
          {forfaits.map((f) => <option key={f.id} value={f.id}>{f.nom}</option>)}
        </select>
      </div>

      {forfaitId ? (
        <div>
          <div className="space-y-2">
            {lignes.map((l, i) => (
              <div key={i} className="flex items-center gap-2 text-sm">
                <select value={l.produit_id} onChange={(e) => majLigne(i, "produit_id", e.target.value)}
                  className="border rounded px-2 py-1 flex-1">
                  {produits.map((p) => (
                    <option key={p.id} value={p.id}>{nomProduit(p.id)}</option>
                  ))}
                </select>
                <span className="text-slate-500">1 unité tous les</span>
                <input type="number" min="1" value={l.lavages_par_unite}
                  onChange={(e) => majLigne(i, "lavages_par_unite", e.target.value)}
                  className="border rounded px-2 py-1 w-20" />
                <span className="text-slate-500">lavages</span>
                <button onClick={() => retirer(i)} className="text-red-600 text-sm ml-1">✕</button>
              </div>
            ))}
            {lignes.length === 0 && (
              <div className="text-slate-400 text-sm">Aucun produit consommé pour ce forfait.</div>
            )}
          </div>
          <div className="flex items-center gap-3 mt-3">
            <button onClick={ajouterLigne} className="text-sm border rounded px-3 py-1.5">+ Ajouter un produit</button>
            <button onClick={enregistrer} className="bg-slate-900 text-white px-4 py-1.5 rounded text-sm">Enregistrer</button>
            {message && <span className="text-sm text-green-700">{message}</span>}
          </div>
        </div>
      ) : (
        <div className="text-slate-400 text-sm">Sélectionnez un forfait.</div>
      )}
    </div>
  );
}
