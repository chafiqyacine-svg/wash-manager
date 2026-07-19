// Configuration : forfaits (prix, zones requises, seuils de temps), zones caméra.
export default function Config() {
  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Configuration</h1>
      {/* TODO(dev):
          - éditer les forfaits via api.forfaits() (prix, zones_requises, temps_min/max).
          - éditer les seuils d'anomalie.
          - (avancé) éditer les coordonnées de zones/lignes des caméras. */}
      <div className="bg-white rounded-lg shadow p-4 text-slate-500">
        À câbler : édition des forfaits et des seuils.
      </div>
    </div>
  );
}
