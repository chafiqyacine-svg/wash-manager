import { useEffect, useState } from "react";
import { api } from "../api/client.js";

const VIDE = { nom: "", unite: "L", quantite: 0, seuil_alerte: 0, prix_unitaire: 0, site_id: "" };

// Inventaire : stock des consommables par site, avec alerte de réapprovisionnement.
export default function Inventory() {
  const [sites, setSites] = useState([]);
  const [siteId, setSiteId] = useState("");
  const [produits, setProduits] = useState([]);
  const [nouveau, setNouveau] = useState(VIDE);
  const [message, setMessage] = useState("");

  useEffect(() => { api.sites().then(setSites).catch(() => {}); }, []);
  const charger = () => api.produits(siteId || undefined).then(setProduits).catch(() => setProduits([]));
  useEffect(() => { charger(); }, [siteId]);

  const nomSite = (id) => sites.find((s) => s.id === id)?.nom ?? "—";
  const bas = (p) => Number(p.quantite) <= Number(p.seuil_alerte);

  const bouger = async (id, delta) => { await api.mouvementProduit(id, delta).catch(() => {}); charger(); };
  const majPrix = async (id, prix) => {
    await api.modifierProduit(id, { prix_unitaire: Number(prix) || 0 }).catch(() => {});
    charger();
  };

  const ajouter = async () => {
    setMessage("");
    try {
      await api.creerProduit({
        nom: nouveau.nom, unite: nouveau.unite,
        quantite: Number(nouveau.quantite), seuil_alerte: Number(nouveau.seuil_alerte),
        prix_unitaire: Number(nouveau.prix_unitaire),
        site_id: nouveau.site_id ? Number(nouveau.site_id) : null,
      });
      setNouveau(VIDE); charger();
    } catch { setMessage("Erreur lors de l'ajout."); }
  };

  const supprimer = async (id) => { await api.supprimerProduit(id).catch(() => {}); charger(); };

  const nbBas = produits.filter(bas).length;

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-bold text-slate-800">Inventaire</h1>
        <select value={siteId} onChange={(e) => setSiteId(e.target.value)}
          className="border rounded-lg px-3 py-2 bg-white text-sm">
          <option value="">Tous les sites</option>
          {sites.map((s) => <option key={s.id} value={s.id}>{s.nom}</option>)}
        </select>
      </div>
      {nbBas > 0 && (
        <div className="mb-3 text-sm bg-amber-50 text-amber-800 rounded-lg px-3 py-2">
          ⚠️ {nbBas} produit(s) sous le seuil de réapprovisionnement.
        </div>
      )}
      {message && <div className="mb-3 text-sm text-red-600">{message}</div>}

      <div className="bg-white rounded-2xl shadow-sm overflow-x-auto mb-4">
        <table className="w-full text-sm">
          <thead className="text-slate-400 text-left">
            <tr>
              <th className="p-3 font-medium">Produit</th>
              <th className="p-3 font-medium">Site</th>
              <th className="p-3 font-medium text-right">Stock</th>
              <th className="p-3 font-medium text-right">Seuil</th>
              <th className="p-3 font-medium text-right">Prix unit.</th>
              <th className="p-3 font-medium text-center">Ajuster</th>
              <th className="p-3 font-medium"></th>
            </tr>
          </thead>
          <tbody>
            {produits.map((p) => (
              <tr key={p.id} className={`border-t border-slate-100 ${bas(p) ? "bg-amber-50" : ""}`}>
                <td className="p-3 font-medium text-slate-700">
                  {p.nom} {bas(p) && <span className="text-amber-600 text-xs">(bas)</span>}
                </td>
                <td className="p-3 text-slate-500">{nomSite(p.site_id)}</td>
                <td className="p-3 text-right">{p.quantite} {p.unite}</td>
                <td className="p-3 text-right text-slate-500">{p.seuil_alerte} {p.unite}</td>
                <td className="p-3 text-right">
                  <input type="number" defaultValue={p.prix_unitaire} step="0.01"
                    onBlur={(e) => Number(e.target.value) !== Number(p.prix_unitaire) && majPrix(p.id, e.target.value)}
                    className="w-20 border rounded px-1 py-0.5 text-right text-slate-600" /> DH
                </td>
                <td className="p-3 text-center whitespace-nowrap">
                  <button onClick={() => bouger(p.id, -1)} className="w-7 h-7 rounded bg-slate-100">−</button>
                  <button onClick={() => bouger(p.id, 1)} className="w-7 h-7 rounded bg-slate-100 ml-1">+</button>
                  <button onClick={() => bouger(p.id, 10)} className="px-2 h-7 rounded bg-slate-100 ml-1 text-xs">+10</button>
                </td>
                <td className="p-3 text-right">
                  <button onClick={() => supprimer(p.id)} className="text-sm text-red-600">Retirer</button>
                </td>
              </tr>
            ))}
            {produits.length === 0 && (
              <tr><td className="p-3 text-slate-400" colSpan={7}>Aucun produit.</td></tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Ajouter un produit */}
      <div className="bg-white rounded-2xl shadow-sm p-4 max-w-3xl">
        <h2 className="font-semibold text-slate-800 mb-2">Ajouter un produit</h2>
        <div className="grid grid-cols-2 md:grid-cols-6 gap-2 text-sm">
          <input className="border rounded px-2 py-1" placeholder="Nom"
            value={nouveau.nom} onChange={(e) => setNouveau({ ...nouveau, nom: e.target.value })} />
          <input className="border rounded px-2 py-1" placeholder="Unité (L, kg…)"
            value={nouveau.unite} onChange={(e) => setNouveau({ ...nouveau, unite: e.target.value })} />
          <input type="number" className="border rounded px-2 py-1" placeholder="Quantité"
            value={nouveau.quantite} onChange={(e) => setNouveau({ ...nouveau, quantite: e.target.value })} />
          <input type="number" className="border rounded px-2 py-1" placeholder="Seuil"
            value={nouveau.seuil_alerte} onChange={(e) => setNouveau({ ...nouveau, seuil_alerte: e.target.value })} />
          <input type="number" step="0.01" className="border rounded px-2 py-1" placeholder="Prix unit. (DH)"
            value={nouveau.prix_unitaire} onChange={(e) => setNouveau({ ...nouveau, prix_unitaire: e.target.value })} />
          <select className="border rounded px-2 py-1" value={nouveau.site_id}
            onChange={(e) => setNouveau({ ...nouveau, site_id: e.target.value })}>
            <option value="">Site…</option>
            {sites.map((s) => <option key={s.id} value={s.id}>{s.nom}</option>)}
          </select>
        </div>
        <button onClick={ajouter} disabled={!nouveau.nom}
          className="mt-3 bg-slate-900 text-white px-4 py-1.5 rounded disabled:opacity-40">
          Ajouter
        </button>
      </div>
    </div>
  );
}
