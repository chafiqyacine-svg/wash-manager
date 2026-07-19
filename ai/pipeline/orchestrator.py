"""Orchestrateur : relie détection → tracking → zones/LPR → événements.

C'est la boucle principale par caméra. Selon le `role` de la caméra, elle émet
les événements adéquats (entrée+plaque, présence en zone, sortie).

SQUELETTE : la structure et l'aiguillage par rôle sont posés ; l'assemblage des
frames réelles et l'inférence sont marqués TODO(dev).
"""
from __future__ import annotations

from datetime import datetime, timezone

from pipeline.detector import Detector
from pipeline.events import Event, EventClient, EventType
from pipeline.lpr import LecteurPlaque
from pipeline.tracker import Tracker
from pipeline.zones import DetecteurLigne, DetecteurZone


def _point_reference(bbox) -> tuple[float, float]:
    """Point de référence d'un véhicule (centre du bas de la bbox)."""
    x1, y1, x2, y2 = bbox
    return ((x1 + x2) / 2, y2)


class CameraWorker:
    """Traite le flux d'UNE caméra selon son rôle."""

    def __init__(self, cam_config: dict, detector: Detector, tracker: Tracker,
                 client: EventClient, lpr: LecteurPlaque | None = None) -> None:
        self.cfg = cam_config
        self.detector = detector
        self.tracker = tracker
        self.client = client
        self.lpr = lpr

        self.role = cam_config["role"]
        self.camera_id = cam_config["id"]

        # Détecteurs géométriques selon le rôle
        self.ligne_entree = (
            DetecteurLigne(*map(tuple, cam_config["ligne_entree"]))
            if self.role == "entree" else None
        )
        self.ligne_sortie = (
            DetecteurLigne(*map(tuple, cam_config["ligne_sortie"]))
            if self.role == "sortie" else None
        )
        self.zone = (
            DetecteurZone([tuple(p) for p in cam_config["polygone"]])
            if self.role == "zone" else None
        )
        self.zone_code = cam_config.get("zone_code")

    def traiter_frame(self, image) -> None:
        """Traite une frame : détecte, suit, évalue zones/lignes, émet events."""
        detections = self.detector.detect(image)
        tracks = self.tracker.update(detections, image)

        for track in tracks:
            point = _point_reference(track.bbox)

            if self.role == "entree" and self.ligne_entree.a_franchi(track.track_id, point):
                self._emit(EventType.ENTREE, track.track_id)
                self._lire_et_emettre_plaque(track.track_id, image)

            elif self.role == "sortie" and self.ligne_sortie.a_franchi(track.track_id, point):
                self._emit(EventType.SORTIE, track.track_id)

            elif self.role == "zone":
                transition = self.zone.maj(track.track_id, point)
                if transition == "enter":
                    self._emit(EventType.ZONE_ENTER, track.track_id, zone=self.zone_code)
                elif transition == "exit":
                    self._emit(EventType.ZONE_EXIT, track.track_id, zone=self.zone_code)

    def _lire_et_emettre_plaque(self, track_id: str, image) -> None:
        if self.lpr is None:
            return
        # TODO(dev): découper la région du véhicule avant LPR pour plus de précision.
        resultat = self.lpr.lire(image)
        self._emit(
            EventType.PLAQUE, track_id,
            plaque=resultat.plaque if resultat.valide else None,
            plaque_confiance=resultat.confiance,
        )

    def _emit(self, type_: EventType, track_id: str, **kwargs) -> None:
        event = Event(
            type=type_,
            track_id=track_id,
            camera_id=self.camera_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            **kwargs,
        )
        self.client.send(event)
