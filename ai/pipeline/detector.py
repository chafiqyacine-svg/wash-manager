"""Détection d'objets (véhicules, plaques) via YOLO.

SQUELETTE : interface stable, inférence à brancher (ultralytics).
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Detection:
    bbox: tuple[float, float, float, float]  # x1, y1, x2, y2
    confiance: float
    classe: str                              # "vehicule" | "plaque" | ...


class Detector:
    def __init__(self, weights_path: str, conf: float = 0.4) -> None:
        self.weights_path = weights_path
        self.conf = conf
        self._model = None

    def load(self) -> None:
        # TODO(dev):
        #   from ultralytics import YOLO
        #   self._model = YOLO(self.weights_path)
        raise NotImplementedError("Charger les poids YOLO ici.")

    def detect(self, image) -> list[Detection]:
        """Retourne les détections d'une image."""
        # TODO(dev): results = self._model(image, conf=self.conf)
        #   convertir en list[Detection].
        raise NotImplementedError
