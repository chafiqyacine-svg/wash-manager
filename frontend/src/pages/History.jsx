// Historique : recherche des transactions (plaque, date, employé, anomalie).
export default function History() {
  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Historique</h1>
      {/* TODO(dev):
          - barre de filtres (plaque, date, employé, conforme, type d'anomalie).
          - tableau paginé via api.transactions("?...").
          - détail d'une transaction (photos entrée/sortie, temps par zone). */}
      <div className="bg-white rounded-lg shadow p-4 text-slate-500">
        À câbler : recherche et tableau des transactions.
      </div>
    </div>
  );
}
