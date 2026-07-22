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
from pipeline.vest import bbox_la_plus_proche, couleur_dominante, snap_couleur
from pipeline.zones import DetecteurLigne, DetecteurZone


def _point_reference(bbox) -> tuple[float, float]:
    """Point de référence d'un véhicule (centre du bas de la bbox)."""
    x1, y1, x2, y2 = bbox
    return ((x1 + x2) / 2, y2)


class CameraWorker:
    """Traite le flux d'UNE caméra selon son rôle."""

    def __init__(self, cam_config: dict, detector: Detector, tracker: Tracker,
                 client: EventClient, lpr: LecteurPlaque | None = None,
                 hysteresis: float = 0.0, zone_confirmations: int = 1) -> None:
        self.cfg = cam_config
        self.detector = detector
        self.tracker = tracker
        self.client = client
        self.lpr = lpr

        self.role = cam_config["role"]
        self.camera_id = cam_config["id"]

        # Anti-faux-positifs (réglables globalement, cf. section `tracking`).
        marge = cam_config.get("hysteresis", hysteresis)
        confirmations = cam_config.get("zone_confirmations", zone_confirmations)

        # Détecteurs géométriques selon le rôle. Le rôle "bay" (une caméra par
        # baie, topologie v1 recommandée) cumule entrée + zones + sortie : le
        # track_id reste stable sur tout le parcours du véhicule.
        self.ligne_entree = (
            DetecteurLigne(*map(tuple, cam_config["ligne_entree"]), marge=marge,
                           sens=cam_config.get("sens_entree", 0))
            if cam_config.get("ligne_entree") and self.role in ("entree", "bay") else None
        )
        self.ligne_sortie = (
            DetecteurLigne(*map(tuple, cam_config["ligne_sortie"]), marge=marge,
                           sens=cam_config.get("sens_sortie", 0))
            if cam_config.get("ligne_sortie") and self.role in ("sortie", "bay") else None
        )
        # Zones surveillées : une seule (rôle "zone") ou plusieurs (rôle "bay").
        self.zones: list[tuple[str, DetecteurZone]] = []
        if self.role == "zone" and cam_config.get("polygone"):
            self.zones.append(
                (cam_config.get("zone_code"),
                 DetecteurZone([tuple(p) for p in cam_config["polygone"]],
                               confirmations=confirmations))
            )
        elif self.role == "bay":
            for z in cam_config.get("zones", []):
                self.zones.append(
                    (z["zone_code"], DetecteurZone([tuple(p) for p in z["polygone"]],
                                                   confirmations=confirmations))
                )
        self.zone_code = cam_config.get("zone_code")

        # Identification du laveur par gilet (caméras de zone uniquement).
        # `palette_gilets` = couleurs enregistrées des employés ("#RRGGBB"),
        # utilisées pour ramener la couleur mesurée à une valeur canonique.
        self.detecter_gilet = bool(cam_config.get("detecter_gilet", False))
        self.palette_gilets = cam_config.get("palette_gilets", [])

        self.site_id = cam_config.get("site_id")
        self.frames_traitees = 0   # compteur pour le heartbeat de supervision
        self.events_envoyes = 0

    def traiter_frame(self, image) -> None:
        """Traite une frame : détecte+suit, évalue lignes/zones, émet les events.

        Uniforme pour tous les rôles : seuls les détecteurs présents s'activent
        (entrée seule, sortie seule, zone(s), ou tout à la fois pour "bay").
        """
        self.frames_traitees += 1
        tracks = self.tracker.update(image)  # détection + suivi (ByteTrack)

        for track in tracks:
            point = _point_reference(track.bbox)
            tid = track.track_id

            if self.ligne_entree and self.ligne_entree.a_franchi(tid, point):
                self._emit(EventType.ENTREE, tid)
                self._lire_et_emettre_plaque(tid, image)

            for code, zone in self.zones:
                transition = zone.maj(tid, point)
                if transition == "enter":
                    self._emit(EventType.ZONE_ENTER, tid, zone=code)
                    self._identifier_laveur(tid, point, image)
                elif transition == "exit":
                    self._emit(EventType.ZONE_EXIT, tid, zone=code)

            if self.ligne_sortie and self.ligne_sortie.a_franchi(tid, point):
                self._emit(EventType.SORTIE, tid)

    def _identifier_laveur(self, track_id: str, vehicule_point, image) -> None:
        """À l'entrée d'un véhicule en zone, identifie le laveur par la couleur
        de son gilet et émet un événement BADGE (couleur_gilet) que le backend
        rapproche de l'employé.

        On associe au véhicule la personne la plus proche (celle qui le lave),
        on mesure la couleur dominante de son torse, puis on la ramène à une
        couleur enregistrée (`snap_couleur`) pour que le rapprochement backend
        (exact) fonctionne malgré le bruit de mesure.
        """
        if not self.detecter_gilet:
            return
        personnes = self.detector.detect_personnes(image)
        idx = bbox_la_plus_proche(vehicule_point, [p.bbox for p in personnes])
        if idx is None:
            return
        rgb = couleur_dominante(image, personnes[idx].bbox)
        couleur = snap_couleur(rgb, self.palette_gilets) if self.palette_gilets \
            else None
        if couleur is None:
            # TODO(dev): pas de correspondance -> journaliser (laveur non identifié).
            return
        self._emit(EventType.BADGE, track_id, couleur_gilet=couleur)

    def _lire_et_emettre_plaque(self, track_id: str, image) -> None:
        if self.lpr is None:
            return
        # TODO(dev): découper la région du véhicule avant LPR pour plus de précision.
        try:
            resultat = self.lpr.lire(image)
        except Exception:  # noqa: BLE001 — OCR indisponible/en erreur : ne pas tuer la boucle
            # On émet quand même une PLAQUE sans valeur : le backend enregistre
            # l'entrée et pourra lever PLAQUE_NON_LUE / demander une saisie manuelle.
            self._emit(EventType.PLAQUE, track_id, plaque=None, plaque_confiance=0.0)
            return
        self._emit(
            EventType.PLAQUE, track_id,
            plaque=resultat.plaque if resultat.valide else None,
            plaque_confiance=resultat.confiance,
        )

    def _cle_suivi(self, track_id: str) -> str:
        """Clé de suivi GLOBALE = caméra + id local du tracker.

        Les trackers numérotent les véhicules localement (1, 2, 3…) et par
        caméra : deux caméras réutilisent les mêmes id pour des véhicules
        différents. On préfixe donc par la caméra pour éviter toute collision
        côté backend (qui corrèle les événements par cette clé).
        """
        return f"{self.camera_id}:{track_id}"

    def heartbeat_payload(self, outbox_en_attente: int = 0) -> dict:
        """Instantané de supervision de cette caméra pour le backend."""
        return {
            "camera_id": self.camera_id,
            "site_id": self.site_id,
            "role": self.role,
            "frames_traitees": self.frames_traitees,
            "events_envoyes": self.events_envoyes,
            "outbox_en_attente": outbox_en_attente,
        }

    def _emit(self, type_: EventType, track_id: str, **kwargs) -> None:
        self.events_envoyes += 1
        event = Event(
            type=type_,
            track_id=self._cle_suivi(track_id),
            camera_id=self.camera_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            **kwargs,
        )
        self.client.send(event)
