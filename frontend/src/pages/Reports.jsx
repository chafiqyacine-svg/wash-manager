// Rapports journaliers : consultation et téléchargement du PDF.
export default function Reports() {
  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Rapports</h1>
      {/* TODO(dev):
          - liste via api.rapports() (date, total véhicules, CA, conformité).
          - lien de téléchargement du PDF (champ fichier_pdf).
          - bouton "Générer maintenant" -> POST /rapports/generer. */}
      <div className="bg-white rounded-lg shadow p-4 text-slate-500">
        À câbler : liste des rapports journaliers et téléchargement PDF.
      </div>
    </div>
  );
}
