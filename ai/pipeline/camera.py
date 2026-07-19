"""Lecture des flux caméra (RTSP/ONVIF via OpenCV).

SQUELETTE : ouvre un flux et itère sur les frames. La reconnexion robuste et le
buffering sont à finir.
"""
from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass


@dataclass
class Frame:
    """Une image + son horodatage."""
    image: object      # np.ndarray (BGR) — non typé ici pour éviter la dépendance numpy
    timestamp: float   # epoch seconds
    camera_id: str


class CameraStream:
    def __init__(self, camera_id: str, source: str) -> None:
        self.camera_id = camera_id
        self.source = source
        self._cap = None

    def open(self) -> None:
        # TODO(dev): import cv2 ; self._cap = cv2.VideoCapture(self.source)
        #   Gérer l'échec d'ouverture et la reconnexion automatique.
        raise NotImplementedError("Brancher OpenCV VideoCapture ici.")

    def frames(self) -> Iterator[Frame]:
        """Génère les frames en continu."""
        # TODO(dev): boucle read() ; yield Frame(...) ; reconnexion si ret=False.
        raise NotImplementedError

    def close(self) -> None:
        if self._cap is not None:
            # self._cap.release()
            self._cap = None
