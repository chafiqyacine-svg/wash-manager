// Employés : liste + métriques de performance + classement (cf. section 8).
export default function Employees() {
  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Employés</h1>
      {/* TODO(dev):
          - liste via api.employes().
          - métriques par employé via api.metriquesEmploye(id)
            (véhicules/jour, temps moyen, taux conformité, revenus, score).
          - classement hebdomadaire (tri par score qualité). */}
      <div className="bg-white rounded-lg shadow p-4 text-slate-500">
        À câbler : tableau des employés et métriques.
      </div>
    </div>
  );
}
