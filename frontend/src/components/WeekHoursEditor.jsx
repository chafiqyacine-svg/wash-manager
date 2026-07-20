import { useEffect, useState } from "react";

// Éditeur d'horaires hebdomadaire réutilisable.
// `champs` = ["heure_ouverture","heure_fermeture"] (site) ou ["debut","fin"] (employé).
const JOURS = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"];

// Convertit "HH:MM:SS" -> "HH:MM" pour l'input time, et inversement à l'envoi.
const court = (t) => (t ? t.slice(0, 5) : "");

function construire(initial, a, b, defaut) {
  const m = {};
  for (let j = 0; j < 7; j++) {
    const ex = initial.find((h) => h.jour === j);
    m[j] = ex
      ? { actif: true, a: court(ex[a]), b: court(ex[b]) }
      : { actif: false, a: defaut.a, b: defaut.b };
  }
  return m;
}

export default function WeekHoursEditor({ initial = [], champs, defaut, onSave }) {
  const [a, b] = champs;
  const [semaine, setSemaine] = useState(() => construire(initial, a, b, defaut));
  const [message, setMessage] = useState("");

  // Resynchronise quand les horaires chargés (async) arrivent/changent.
  useEffect(() => {
    setSemaine(construire(initial, a, b, defaut));
  }, [initial]); // eslint-disable-line react-hooks/exhaustive-deps

  const set = (j, key, val) => setSemaine((s) => ({ ...s, [j]: { ...s[j], [key]: val } }));

  const enregistrer = async () => {
    setMessage("");
    const horaires = [];
    for (let j = 0; j < 7; j++) {
      if (semaine[j].actif) horaires.push({ jour: j, [a]: semaine[j].a, [b]: semaine[j].b });
    }
    try {
      await onSave(horaires);
      setMessage("Horaires enregistrés.");
    } catch {
      setMessage("Erreur.");
    }
  };

  return (
    <div>
      <div className="space-y-1">
        {JOURS.map((nom, j) => (
          <div key={j} className="flex items-center gap-3 text-sm">
            <label className="w-28 flex items-center gap-2">
              <input type="checkbox" checked={semaine[j].actif}
                onChange={(e) => set(j, "actif", e.target.checked)} />
              {nom}
            </label>
            <input type="time" disabled={!semaine[j].actif} value={semaine[j].a}
              onChange={(e) => set(j, "a", e.target.value)}
              className="border rounded px-2 py-1 disabled:opacity-40" />
            <span className="text-slate-400">→</span>
            <input type="time" disabled={!semaine[j].actif} value={semaine[j].b}
              onChange={(e) => set(j, "b", e.target.value)}
              className="border rounded px-2 py-1 disabled:opacity-40" />
          </div>
        ))}
      </div>
      <div className="flex items-center gap-3 mt-3">
        <button onClick={enregistrer} className="bg-slate-900 text-white px-4 py-1.5 rounded text-sm">
          Enregistrer
        </button>
        {message && <span className="text-sm text-green-700">{message}</span>}
      </div>
    </div>
  );
}
