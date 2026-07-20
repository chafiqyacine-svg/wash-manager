import { useEffect, useRef, useState } from "react";
import { api } from "../api/client.js";

// Pointage : l'employé se prend en selfie EN DIRECT (caméra) au début de sa
// journée. Le serveur horodate la réception — l'heure fait foi (anti-fraude :
// impossible de réutiliser une ancienne photo).
export default function Pointage() {
  const videoRef = useRef(null);
  const [employes, setEmployes] = useState([]);
  const [employeId, setEmployeId] = useState("");
  const [type, setType] = useState("arrivee");
  const [pointages, setPointages] = useState([]);
  const [message, setMessage] = useState("");
  const [cameraPrete, setCameraPrete] = useState(false);

  useEffect(() => { api.employes().then(setEmployes).catch(() => {}); rafraichir(); }, []);
  const rafraichir = () => api.pointages().then(setPointages).catch(() => {});

  // Ouvre la caméra frontale (selfie).
  useEffect(() => {
    let stream;
    navigator.mediaDevices?.getUserMedia({ video: { facingMode: "user" } })
      .then((s) => {
        stream = s;
        if (videoRef.current) { videoRef.current.srcObject = s; setCameraPrete(true); }
      })
      .catch(() => setMessage("Caméra indisponible (autorisez l'accès)."));
    return () => stream?.getTracks().forEach((t) => t.stop());
  }, []);

  const capturerEtPointer = async () => {
    if (!employeId) { setMessage("Sélectionnez l'employé."); return; }
    setMessage("");
    const video = videoRef.current;
    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth || 320;
    canvas.height = video.videoHeight || 240;
    canvas.getContext("2d").drawImage(video, 0, 0, canvas.width, canvas.height);
    const blob = await new Promise((r) => canvas.toBlob(r, "image/jpeg", 0.85));
    try {
      const res = await api.pointer(Number(employeId), type, blob);
      const h = new Date(res.heure).toLocaleString();
      setMessage(`Pointage enregistré à ${h}.`);
      rafraichir();
    } catch {
      setMessage("Erreur lors du pointage.");
    }
  };

  return (
    <div>
      <h1 className="text-2xl font-bold text-slate-800 mb-4">Pointage</h1>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Capture selfie */}
        <div className="bg-white rounded-2xl shadow-sm p-4">
          <div className="bg-black rounded-xl overflow-hidden aspect-video mb-3">
            <video ref={videoRef} autoPlay playsInline muted className="w-full h-full object-cover" />
          </div>
          <div className="flex flex-wrap gap-2 items-center">
            <select value={employeId} onChange={(e) => setEmployeId(e.target.value)}
              className="border rounded-lg px-3 py-2 text-sm">
              <option value="">Employé…</option>
              {employes.map((e) => <option key={e.id} value={e.id}>{e.nom}</option>)}
            </select>
            <select value={type} onChange={(e) => setType(e.target.value)}
              className="border rounded-lg px-3 py-2 text-sm">
              <option value="arrivee">Arrivée</option>
              <option value="depart">Départ</option>
            </select>
            <button onClick={capturerEtPointer} disabled={!cameraPrete}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm disabled:opacity-40">
              📸 Pointer
            </button>
          </div>
          {message && <div className="mt-2 text-sm text-slate-600">{message}</div>}
        </div>

        {/* Derniers pointages */}
        <div className="bg-white rounded-2xl shadow-sm p-4">
          <h2 className="font-semibold text-slate-800 mb-3">Derniers pointages</h2>
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {pointages.map((p) => (
              <div key={p.id} className="flex items-center gap-3 border border-slate-100 rounded-lg p-2">
                {p.photo_url && (
                  <img src={p.photo_url} alt="selfie" className="w-12 h-12 rounded object-cover" />
                )}
                <div className="flex-1 text-sm">
                  <div className="font-medium text-slate-700">{p.employe}</div>
                  <div className="text-slate-400 text-xs">
                    {p.type === "depart" ? "Départ" : "Arrivée"} · {new Date(p.heure).toLocaleString()}
                  </div>
                </div>
              </div>
            ))}
            {pointages.length === 0 && <div className="text-slate-400 text-sm">Aucun pointage.</div>}
          </div>
        </div>
      </div>
    </div>
  );
}
