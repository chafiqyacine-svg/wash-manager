# Pipeline IA (edge) — détection, tracking, LPR, zones

Ce module tourne sur le **serveur edge** (Jetson Orin Nano / mini-PC + GPU) au
plus près des caméras. Il lit les flux RTSP/ONVIF, détecte et suit chaque
véhicule, lit les plaques, et **émet des événements** vers le backend
(`POST /api/v1/events`). Il ne contient AUCUNE logique métier (classification,
anomalies) : celle-ci vit dans le backend.

## Chaîne de traitement

```
  Flux caméra (RTSP)
        │
        ▼
   [detector]  YOLOv8/YOLO11 → bounding boxes véhicules
        │
        ▼
   [tracker]   DeepSORT/ByteTrack → track_id stable par véhicule
        │
        ├─► [zones]  franchissement lignes (A entrée / E sortie) + présence zones B/C/D
        │
        └─► [lpr]    à l'entrée : détection plaque + OCR (plaques marocaines)
        │
        ▼
   [orchestrator] agrège par track_id → construit les EventIn
        │
        ▼
   [events] POST vers le backend (clé X-AI-Key)
```

## Fichiers

| Fichier                 | Rôle                                                        |
|-------------------------|-------------------------------------------------------------|
| `pipeline/camera.py`    | Ouverture/lecture des flux caméra (OpenCV/RTSP).            |
| `pipeline/detector.py`  | Wrapper YOLO (détection véhicules + plaques).               |
| `pipeline/tracker.py`   | Suivi multi-objets (track_id stable).                      |
| `pipeline/zones.py`     | Lignes virtuelles & polygones de zones, logique de présence.|
| `pipeline/lpr.py`       | Pipeline LPR : crop → prétraitement → OCR → validation.    |
| `pipeline/events.py`    | Modèle d'événement + client HTTP vers le backend.          |
| `pipeline/orchestrator.py` | Boucle principale : relie détection→tracking→zones→events. |
| `config.yaml`           | Caméras, zones (coordonnées), forfaits, seuils.            |
| `run.py`                | Lanceur : `python run.py --config config.yaml`.            |

## Points à finir (`TODO(dev)`)

- Charger les poids YOLO réels (`ai/models/`) et le modèle LPR marocain.
- Calibrer les coordonnées des lignes/zones dans `config.yaml` par caméra.
- Entraîner/affiner l'OCR sur les caractères arabes des plaques marocaines.
- Régler le tracking (ré-identification inter-caméras si multi-flux).

## Tester la détection SANS caméras (sur une vidéo)

Avant l'installation, on peut valider la détection de véhicules sur une simple
vidéo (filmée au téléphone) avec les poids YOLO pré-entraînés (classe « voiture »
déjà connue). Aucun matériel requis.

```bash
pip install ultralytics opencv-python
cd ai
python detect_video.py --video ma_video.mp4 --out annote.mp4
# avec comptage sur une ligne virtuelle (x1,y1,x2,y2 en pixels) :
python detect_video.py --video ma_video.mp4 --ligne 0,540,1920,540 --out annote.mp4
```

`Detector`, `Tracker` (ByteTrack via ultralytics) et `CameraStream` sont
fonctionnels. `detect_video.py` **suit** chaque véhicule (track_id) pour un
comptage fiable (pas de double comptage) et peut **émettre des événements** vers
le backend comme une vraie caméra :

```bash
# comptage seul (vidéo annotée)
python detect_video.py --video lavage.mp4 --ligne 0,540,1920,540 --out annote.mp4
# + émission d'événements ENTREE vers le backend
python detect_video.py --video lavage.mp4 --ligne 0,540,1920,540 --emit \
    --backend http://localhost:8000 --ingest-key change-me-ingest-key
```

`CameraStream` accepte une URL RTSP **ou** un chemin de fichier vidéo comme `source`.

## Dépendances (voir requirements.txt)

Volumineuses (torch, ultralytics…). À installer sur la machine edge selon
l'accélérateur (CUDA / TensorRT / Coral).
