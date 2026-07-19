"""Lecture des flux caméra ET des fichiers vidéo (OpenCV).

`source` peut être une URL RTSP (`rtsp://…`) OU un chemin de fichier vidéo
(`ma_video.mp4`) — ce qui permet de tester le pipeline sur une vidéo filmée au
téléphone avant l'installation des caméras.
"""
from __future__ import annotations

import time
from collections.abc import Iterator
from dataclasses import dataclass


@dataclass
class Frame:
    """Une image + son horodatage."""
    image: object      # np.ndarray (BGR)
    timestamp: float   # epoch seconds
    camera_id: str


class CameraStream:
    def __init__(self, camera_id: str, source: str, reconnect: bool = True) -> None:
        self.camera_id = camera_id
        self.source = source
        self.reconnect = reconnect  # utile pour le RTSP, pas pour un fichier
        self._cap = None

    def open(self) -> None:
        import cv2
        self._cap = cv2.VideoCapture(self.source)
        if not self._cap.isOpened():
            raise RuntimeError(f"Impossible d'ouvrir la source : {self.source}")

    def frames(self) -> Iterator[Frame]:
        if self._cap is None:
            self.open()
        while True:
            ret, image = self._cap.read()
            if not ret:
                # Fin de fichier vidéo, ou flux interrompu.
                if self.reconnect and self.source.startswith("rtsp"):
                    self.close()
                    time.sleep(1)
                    self.open()
                    continue
                break
            yield Frame(image=image, timestamp=time.time(), camera_id=self.camera_id)

    def close(self) -> None:
        if self._cap is not None:
            self._cap.release()
            self._cap = None
