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

## Dépendances (voir requirements.txt)

Non installées par défaut (volumineuses : torch, ultralytics…). À installer sur
la machine edge selon l'accélérateur (CUDA / TensorRT / Coral).
