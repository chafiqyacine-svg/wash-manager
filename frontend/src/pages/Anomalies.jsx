// Anomalies : liste, filtrage par sévérité/statut, résolution.
export default function Anomalies() {
  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Anomalies</h1>
      {/* TODO(dev):
          - liste via api.anomalies("?resolu=false") avec badge de sévérité.
          - bouton "Résoudre" -> api.resoudreAnomalie(id).
          - aperçu photo + lien vers la transaction. */}
      <div className="bg-white rounded-lg shadow p-4 text-slate-500">
        À câbler : liste des anomalies et actions de résolution.
      </div>
    </div>
  );
}
