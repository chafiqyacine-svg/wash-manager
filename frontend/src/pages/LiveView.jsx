// Vue temps réel : flux caméras avec overlay IA (zones, compteurs).
export default function LiveView() {
  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Temps réel</h1>
      {/* TODO(dev):
          - afficher une grille de flux caméra (HLS/WebRTC) — cf. section 10.3.
          - superposer les zones/lignes et les compteurs par caméra.
          - s'abonner au WebSocket /api/v1/ws/live pour les positions véhicules. */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {["Entrée (LPR)", "Lavage", "Aspiration", "Polish", "Sortie"].map((c) => (
          <div key={c} className="bg-black text-white aspect-video rounded flex items-center justify-center">
            {c} — flux à intégrer
          </div>
        ))}
      </div>
    </div>
  );
}
