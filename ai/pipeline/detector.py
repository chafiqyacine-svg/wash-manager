"""Détection d'objets (véhicules, plaques) via YOLO (ultralytics).

Implémentation fonctionnelle : avec `pip install ultralytics` et un fichier de
poids (les poids COCO pré-entraînés `yolov8n.pt` se téléchargent tout seuls au
premier appel), la détection de véhicules marche immédiatement — utile pour
tester sur une vidéo AVANT l'installation des caméras (voir detect_video.py).

Pour la détection de plaques, fournir des poids entraînés sur les plaques
(classe « plaque ») — voir TODO(dev).
"""
from __future__ import annotations

from dataclasses import dataclass

# Classes COCO correspondant à des véhicules.
CLASSES_VEHICULE = {"car", "truck", "bus", "motorcycle"}
# Classe COCO d'une personne (laveur) — sert à l'identification par gilet.
CLASSES_PERSONNE = {"person"}


@dataclass
class Detection:
    bbox: tuple[float, float, float, float]  # x1, y1, x2, y2
    confiance: float
    classe: str                              # "car", "truck", "plaque", ...


class Detector:
    def __init__(self, weights_path: str = "yolov8n.pt", conf: float = 0.4) -> None:
        self.weights_path = weights_path
        self.conf = conf
        self._model = None

    def load(self) -> None:
        # Import local : ultralytics n'est requis que sur la machine edge.
        from ultralytics import YOLO
        self._model = YOLO(self.weights_path)

    def detect(self, image, classes: set[str] | None = None) -> list[Detection]:
        """Détections d'une image (filtrées sur `classes` si fourni)."""
        if self._model is None:
            self.load()
        resultats = self._model(image, conf=self.conf, verbose=False)[0]
        noms = self._model.names
        detections: list[Detection] = []
        for box in resultats.boxes:
            classe = noms[int(box.cls)]
            if classes and classe not in classes:
                continue
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            detections.append(Detection((x1, y1, x2, y2), float(box.conf), classe))
        return detections

    def detect_vehicules(self, image) -> list[Detection]:
        return self.detect(image, classes=CLASSES_VEHICULE)

    def detect_personnes(self, image) -> list[Detection]:
        """Détecte les personnes (laveurs) — pour l'identification par gilet."""
        return self.detect(image, classes=CLASSES_PERSONNE)
