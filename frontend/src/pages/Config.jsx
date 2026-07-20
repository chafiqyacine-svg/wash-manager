import { useEffect, useState } from "react";
import { api } from "../api/client.js";
import RecetteEditor from "../components/RecetteEditor.jsx";
import WeekHoursEditor from "../components/WeekHoursEditor.jsx";

const ZONES = [
  { code: "B", label: "Lavage ext." },
  { code: "C", label: "Aspiration" },
  { code: "D", label: "Polish/Cire" },
];

// Configuration : paramètres réglables (fenêtre de rapprochement) + forfaits.
const NOUVEAU_VIDE = { nom: "", prix: "", temps_min: "", temps_max: "", zones_requises: ["B"], produits: [] };

export default function Config() {
  const [fenetre, setFenetre] = useState("");
  const [forfaits, setForfaits] = useState([]);
  const [nouveau, setNouveau] = useState(NOUVEAU_VIDE);
  const [message, setMessage] = useState("");
  // Horaires d'ouverture
  const [sites, setSites] = useState([]);
  const [siteHoraires, setSiteHoraires] = useState("");
  const [horaires, setHoraires] = useState([]);
  const [produits, setProduits] = useState([]);

  const charger = () => {
    api.parametres().then((p) => setFenetre(p.fenetre_rapprochement_minutes ?? "30")).catch(() => {});
    api.forfaits().then(setForfaits).catch(() => {});
    api.sites().then(setSites).catch(() => {});
    api.produits().then(setProduits).catch(() => {});
  };
  useEffect(charger, []);

  useEffect(() => {
    if (siteHoraires) api.horairesSite(siteHoraires).then(setHoraires).catch(() => setHoraires([]));
  }, [siteHoraires]);

  const supprimerForfait = async (f) => {
    setMessage("");
    try {
      await api.supprimerForfait(f.id);
      setMessage(`Forfait ${f.nom} supprimé.`);
      charger();
    } catch {
      setMessage(`Impossible de supprimer ${f.nom} (déjà utilisé dans l'historique).`);
    }
  };

  const creerService = async () => {
    setMessage("");
    try {
      const forfait = await api.creerForfait({
        nom: nouveau.nom,
        prix: Number(nouveau.prix),
        temps_min: Number(nouveau.temps_min),
        temps_max: Number(nouveau.temps_max),
        zones_requises: nouveau.zones_requises,
      });
      // Recette de consommation saisie en même temps que le service.
      const recette = nouveau.produits
        .filter((p) => p.produit_id)
        .map((p) => ({ produit_id: Number(p.produit_id), lavages_par_unite: Number(p.lavages_par_unite) }));
      if (recette.length) await api.majConsommation(forfait.id, recette);
      setMessage(`Service ${nouveau.nom} créé.`);
      setNouveau(NOUVEAU_VIDE);
      charger();
    } catch {
      setMessage("Erreur lors de la création du service (nom déjà pris ?).");
    }
  };

  // Lignes de produits consommés du nouveau service
  const ajouterProduitNouveau = () =>
    setNouveau((n) => ({ ...n, produits: [...n.produits, { produit_id: produits[0]?.id ?? "", lavages_par_unite: 20 }] }));
  const majProduitNouveau = (i, champ, val) =>
    setNouveau((n) => ({ ...n, produits: n.produits.map((p, j) => (j === i ? { ...p, [champ]: val } : p)) }));
  const retirerProduitNouveau = (i) =>
    setNouveau((n) => ({ ...n, produits: n.produits.filter((_, j) => j !== i) }));

  const toggleZoneNouveau = (code) =>
    setNouveau((n) => ({
      ...n,
      zones_requises: n.zones_requises.includes(code)
        ? n.zones_requises.filter((z) => z !== code)
        : [...n.zones_requises, code],
    }));

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
                <div className="flex gap-2">
                  <button
                    onClick={() => enregistrerForfait(f)}
                    className="text-sm bg-slate-900 text-white px-3 py-1 rounded"
                  >
                    Enregistrer
                  </button>
                  <button
                    onClick={() => supprimerForfait(f)}
                    className="text-sm border border-red-300 text-red-700 px-3 py-1 rounded"
                  >
                    Supprimer
                  </button>
                </div>
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

        {/* Ajout d'un nouveau service */}
        <div className="border-t mt-4 pt-4">
          <h3 className="font-medium mb-2">Ajouter un service</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
            <input
              className="border rounded px-2 py-1"
              placeholder="Nom (ex: VIP)"
              value={nouveau.nom}
              onChange={(e) => setNouveau({ ...nouveau, nom: e.target.value })}
            />
            <input
              type="number" className="border rounded px-2 py-1" placeholder="Prix"
              value={nouveau.prix}
              onChange={(e) => setNouveau({ ...nouveau, prix: e.target.value })}
            />
            <input
              type="number" className="border rounded px-2 py-1" placeholder="Temps min"
              value={nouveau.temps_min}
              onChange={(e) => setNouveau({ ...nouveau, temps_min: e.target.value })}
            />
            <input
              type="number" className="border rounded px-2 py-1" placeholder="Temps max"
              value={nouveau.temps_max}
              onChange={(e) => setNouveau({ ...nouveau, temps_max: e.target.value })}
            />
          </div>
          <div className="mt-2 flex items-center gap-3 text-sm">
            {ZONES.map((z) => (
              <label key={z.code} className="flex items-center gap-1">
                <input
                  type="checkbox"
                  checked={nouveau.zones_requises.includes(z.code)}
                  onChange={() => toggleZoneNouveau(z.code)}
                />
                {z.label}
              </label>
            ))}
          </div>

          {/* Produits consommés par ce service (recette) */}
          <div className="mt-3 border-t pt-3">
            <div className="text-sm font-medium text-slate-600 mb-2">Produits consommés</div>
            <div className="space-y-2">
              {nouveau.produits.map((p, i) => (
                <div key={i} className="flex items-center gap-2 text-sm">
                  <select value={p.produit_id}
                    onChange={(e) => majProduitNouveau(i, "produit_id", e.target.value)}
                    className="border rounded px-2 py-1 flex-1">
                    {produits.map((pr) => (
                      <option key={pr.id} value={pr.id}>{pr.nom} ({pr.unite})</option>
                    ))}
                  </select>
                  <span className="text-slate-500">1 unité tous les</span>
                  <input type="number" min="1" value={p.lavages_par_unite}
                    onChange={(e) => majProduitNouveau(i, "lavages_par_unite", e.target.value)}
                    className="border rounded px-2 py-1 w-20" />
                  <span className="text-slate-500">lavages</span>
                  <button onClick={() => retirerProduitNouveau(i)} className="text-red-600 ml-1">✕</button>
                </div>
              ))}
            </div>
            <button onClick={ajouterProduitNouveau}
              className="mt-2 text-sm border rounded px-3 py-1.5" disabled={produits.length === 0}>
              + Ajouter un produit
            </button>
          </div>

          <div className="mt-3 flex">
            <button
              onClick={creerService}
              disabled={!nouveau.nom}
              className="ml-auto bg-slate-900 text-white px-4 py-1.5 rounded disabled:opacity-40"
            >
              Ajouter le service
            </button>
          </div>
        </div>
      </div>

      {/* Horaires d'ouverture par site */}
      <div className="bg-white rounded-2xl shadow-sm p-4 mt-6 max-w-xl">
        <div className="flex items-center justify-between mb-3">
          <h2 className="font-semibold text-slate-800">Horaires d'ouverture</h2>
          <select value={siteHoraires} onChange={(e) => setSiteHoraires(e.target.value)}
            className="border rounded-lg px-3 py-1.5 text-sm">
            <option value="">Choisir un site…</option>
            {sites.map((s) => <option key={s.id} value={s.id}>{s.nom}</option>)}
          </select>
        </div>
        {siteHoraires ? (
          <WeekHoursEditor
            key={siteHoraires}
            initial={horaires}
            champs={["heure_ouverture", "heure_fermeture"]}
            defaut={{ a: "08:00", b: "20:00" }}
            onSave={(h) => api.majHorairesSite(siteHoraires, h)}
          />
        ) : (
          <div className="text-slate-400 text-sm">Sélectionnez un site pour éditer ses horaires.</div>
        )}
      </div>

      {/* Consommation produits par forfait */}
      <RecetteEditor />
    </div>
  );
}
