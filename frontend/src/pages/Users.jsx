import { useEffect, useState } from "react";
import { api } from "../api/client.js";

const VIDE = { email: "", nom: "", password: "", role: "manager", site_id: "" };
const ROLES = ["admin", "manager", "caissier"];

// Utilisateurs (admin uniquement) : liste + création + activation/rôle.
export default function Users() {
  const [users, setUsers] = useState([]);
  const [sites, setSites] = useState([]);
  const [nouveau, setNouveau] = useState(VIDE);
  const [message, setMessage] = useState("");

  const charger = () => {
    api.users().then(setUsers).catch(() => setUsers([]));
    api.sites().then(setSites).catch(() => {});
  };
  useEffect(charger, []);

  const nomSite = (id) => sites.find((s) => s.id === id)?.nom ?? "Tous";

  const creer = async () => {
    setMessage("");
    try {
      await api.creerUser({
        email: nouveau.email, nom: nouveau.nom, password: nouveau.password,
        role: nouveau.role, site_id: nouveau.site_id ? Number(nouveau.site_id) : null,
      });
      setNouveau(VIDE);
      charger();
    } catch {
      setMessage("Erreur (email déjà pris ?).");
    }
  };

  const basculerActif = async (u) => {
    await api.modifierUser(u.id, { actif: !u.actif }).catch(() => {});
    charger();
  };

  const changerRole = async (u, role) => {
    await api.modifierUser(u.id, { role }).catch(() => {});
    charger();
  };

  return (
    <div>
      <h1 className="text-2xl font-bold text-slate-800 mb-4">Utilisateurs</h1>
      {message && <div className="mb-3 text-sm text-red-600">{message}</div>}

      <div className="bg-white rounded-2xl shadow-sm overflow-x-auto mb-4">
        <table className="w-full text-sm">
          <thead className="text-slate-400 text-left">
            <tr>
              <th className="p-3 font-medium">Nom</th>
              <th className="p-3 font-medium">Email</th>
              <th className="p-3 font-medium">Rôle</th>
              <th className="p-3 font-medium">Site</th>
              <th className="p-3 font-medium">Actif</th>
            </tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.id} className="border-t border-slate-100">
                <td className="p-3 font-medium text-slate-700">{u.nom}</td>
                <td className="p-3 text-slate-600">{u.email}</td>
                <td className="p-3">
                  <select value={u.role} onChange={(e) => changerRole(u, e.target.value)}
                    className="border rounded px-2 py-1">
                    {ROLES.map((r) => <option key={r} value={r}>{r}</option>)}
                  </select>
                </td>
                <td className="p-3 text-slate-600">{nomSite(u.site_id)}</td>
                <td className="p-3">
                  <button onClick={() => basculerActif(u)}
                    className={`text-xs px-2 py-0.5 rounded ${u.actif ? "bg-emerald-100 text-emerald-700" : "bg-slate-200 text-slate-600"}`}>
                    {u.actif ? "Actif" : "Inactif"}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Créer un utilisateur */}
      <div className="bg-white rounded-2xl shadow-sm p-4 max-w-3xl">
        <h2 className="font-semibold text-slate-800 mb-2">Ajouter un utilisateur</h2>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-2 text-sm">
          <input className="border rounded px-2 py-1" placeholder="Nom"
            value={nouveau.nom} onChange={(e) => setNouveau({ ...nouveau, nom: e.target.value })} />
          <input className="border rounded px-2 py-1" placeholder="Email"
            value={nouveau.email} onChange={(e) => setNouveau({ ...nouveau, email: e.target.value })} />
          <input className="border rounded px-2 py-1" type="password" placeholder="Mot de passe"
            value={nouveau.password} onChange={(e) => setNouveau({ ...nouveau, password: e.target.value })} />
          <select className="border rounded px-2 py-1" value={nouveau.role}
            onChange={(e) => setNouveau({ ...nouveau, role: e.target.value })}>
            {ROLES.map((r) => <option key={r} value={r}>{r}</option>)}
          </select>
          <select className="border rounded px-2 py-1" value={nouveau.site_id}
            onChange={(e) => setNouveau({ ...nouveau, site_id: e.target.value })}>
            <option value="">Tous les sites</option>
            {sites.map((s) => <option key={s.id} value={s.id}>{s.nom}</option>)}
          </select>
        </div>
        <button onClick={creer} disabled={!nouveau.email || !nouveau.password}
          className="mt-3 bg-slate-900 text-white px-4 py-1.5 rounded disabled:opacity-40">
          Créer
        </button>
      </div>
    </div>
  );
}
