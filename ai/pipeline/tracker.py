"""Suivi multi-objets : attribue un `track_id` stable à chaque véhicule.

SQUELETTE : interface commune pour ByteTrack (intégré ultralytics) ou DeepSORT.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Track:
    track_id: str
    bbox: tuple[float, float, float, float]
    classe: str


class Tracker:
    def __init__(self, type_: str = "bytetrack", max_age: int = 30) -> None:
        self.type = type_
        self.max_age = max_age
        self._impl = None

    def load(self) -> None:
        # TODO(dev): initialiser ByteTrack/DeepSORT selon self.type.
        raise NotImplementedError

    def update(self, detections, image=None) -> list[Track]:
        """Associe les détections courantes aux pistes existantes."""
        # TODO(dev): retourner la liste des Track avec track_id persistants.
        raise NotImplementedError
