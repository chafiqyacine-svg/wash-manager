import { useEffect, useState } from "react";
import { api } from "../api/client.js";

// Customer Management : véhicules connus (par plaque) et fréquence de visite.
export default function Vehicules() {
  const [vehicules, setVehicules] = useState([]);
  const [q, setQ] = useState("");

  const charger = () => api.vehicules(q).then(setVehicules).catch(() => setVehicules([]));
  useEffect(charger, []);

  return (
    <div>
      <h1 className="text-2xl font-bold text-slate-800 mb-4">Customer Management</h1>
      <div className="flex gap-2 mb-4">
        <input
          className="border rounded-lg px-3 py-2 text-sm"
          placeholder="Rechercher une plaque…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
        <button onClick={charger} className="bg-slate-900 text-white px-4 py-2 rounded-lg text-sm">
          Rechercher
        </button>
      </div>
      <div className="bg-white rounded-2xl shadow-sm overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="text-slate-400 text-left">
            <tr>
              <th className="p-3 font-medium">Plaque</th>
              <th className="p-3 font-medium">Visites</th>
              <th className="p-3 font-medium">Dernière visite</th>
            </tr>
          </thead>
          <tbody>
            {vehicules.map((v) => (
              <tr key={v.id} className="border-t border-slate-100">
                <td className="p-3 font-medium text-slate-700">{v.plaque}</td>
                <td className="p-3 text-slate-600">{v.nombre_visites}</td>
                <td className="p-3 text-slate-600">
                  {v.derniere_visite ? new Date(v.derniere_visite).toLocaleDateString() : "—"}
                </td>
              </tr>
            ))}
            {vehicules.length === 0 && (
              <tr><td className="p-3 text-slate-400" colSpan={3}>Aucun véhicule.</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
