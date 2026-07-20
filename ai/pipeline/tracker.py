"""Suivi multi-objets : `track_id` stable par véhicule (ByteTrack via ultralytics).

Implémentation fonctionnelle : ultralytics intègre ByteTrack/BoT-SORT. On appelle
`model.track(frame, persist=True)` qui renvoie des identifiants persistants.
Nécessite les mêmes poids que la détection.
"""
from __future__ import annotations

from dataclasses import dataclass

from pipeline.detector import CLASSES_VEHICULE


@dataclass
class Track:
    track_id: str
    bbox: tuple[float, float, float, float]
    classe: str


class Tracker:
    """Suivi de véhicules basé sur ultralytics `.track()`."""

    def __init__(self, weights_path: str = "yolov8n.pt", conf: float = 0.4,
                 tracker_cfg: str = "bytetrack.yaml") -> None:
        self.weights_path = weights_path
        self.conf = conf
        self.tracker_cfg = tracker_cfg
        self._model = None

    def load(self) -> None:
        from ultralytics import YOLO
        self._model = YOLO(self.weights_path)

    def update(self, frame) -> list[Track]:
        """Détecte + suit les véhicules d'une frame ; renvoie les pistes actives."""
        if self._model is None:
            self.load()
        resultats = self._model.track(
            frame, persist=True, conf=self.conf, tracker=self.tracker_cfg, verbose=False
        )[0]
        noms = self._model.names
        tracks: list[Track] = []
        if resultats.boxes is None or resultats.boxes.id is None:
            return tracks
        for box in resultats.boxes:
            classe = noms[int(box.cls)]
            if classe not in CLASSES_VEHICULE:
                continue
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            tid = str(int(box.id))
            tracks.append(Track(track_id=tid, bbox=(x1, y1, x2, y2), classe=classe))
        return tracks
