"""Test de câblage de l'orchestrateur : émission de l'identification par gilet.

Vérifie qu'une caméra de zone, à l'entrée d'un véhicule, émet bien un événement
BADGE portant la couleur de gilet canonique (rapprochable par le backend).
Les dépendances lourdes (YOLO, numpy) sont remplacées par des stubs.
"""
from types import SimpleNamespace

import pipeline.orchestrator as orch
from pipeline.events import EventType
from pipeline.orchestrator import CameraWorker


class FakeTracker:
    def __init__(self, tracks):
        self._tracks = tracks

    def update(self, image):
        return self._tracks


class FakeDetector:
    def __init__(self, personnes):
        self._personnes = personnes

    def detect_personnes(self, image):
        return self._personnes


class FakeClient:
    def __init__(self):
        self.events = []

    def send(self, event):
        self.events.append(event)
        return True


CONFIG_ZONE = {
    "id": "cam_zone_b", "role": "zone", "zone_code": "B",
    "polygone": [[0, 0], [500, 0], [500, 500], [0, 500]],
    "detecter_gilet": True, "palette_gilets": ["#E11D48", "#2563EB"],
}


def test_zone_emet_zone_enter_puis_badge_gilet(monkeypatch):
    # Le laveur mesuré en rouge bruité -> ramené à #E11D48 (gilet enregistré).
    monkeypatch.setattr(orch, "couleur_dominante", lambda img, bbox: (220, 35, 70))

    vehicule = SimpleNamespace(track_id="v1", bbox=(100, 100, 200, 200), classe="car")
    laveur = SimpleNamespace(bbox=(150, 150, 190, 260), confiance=0.8, classe="person")

    worker = CameraWorker(
        CONFIG_ZONE, detector=FakeDetector([laveur]),
        tracker=FakeTracker([vehicule]), client=(client := FakeClient()),
    )
    worker.traiter_frame(image=object())  # image factice (stubs)

    types = [e.type for e in client.events]
    assert EventType.ZONE_ENTER in types
    assert EventType.BADGE in types
    badge = next(e for e in client.events if e.type == EventType.BADGE)
    assert badge.couleur_gilet == "#E11D48"
    assert badge.track_id == "v1"


def test_pas_de_badge_sans_personne(monkeypatch):
    monkeypatch.setattr(orch, "couleur_dominante", lambda img, bbox: (220, 35, 70))
    vehicule = SimpleNamespace(track_id="v1", bbox=(100, 100, 200, 200), classe="car")
    worker = CameraWorker(
        CONFIG_ZONE, detector=FakeDetector([]),  # aucun laveur détecté
        tracker=FakeTracker([vehicule]), client=(client := FakeClient()),
    )
    worker.traiter_frame(image=object())
    assert all(e.type != EventType.BADGE for e in client.events)


def test_pas_de_badge_si_couleur_inconnue(monkeypatch):
    # Gris neutre -> hors seuil -> aucun gilet reconnu -> pas de BADGE.
    monkeypatch.setattr(orch, "couleur_dominante", lambda img, bbox: (128, 128, 128))
    vehicule = SimpleNamespace(track_id="v1", bbox=(100, 100, 200, 200), classe="car")
    laveur = SimpleNamespace(bbox=(150, 150, 190, 260), confiance=0.8, classe="person")
    worker = CameraWorker(
        CONFIG_ZONE, detector=FakeDetector([laveur]),
        tracker=FakeTracker([vehicule]), client=(client := FakeClient()),
    )
    worker.traiter_frame(image=object())
    assert all(e.type != EventType.BADGE for e in client.events)


class _LPRQuiCasse:
    """LPR dont l'OCR n'est pas branché (lève, comme NotImplementedError)."""
    def lire(self, image):
        raise NotImplementedError("OCR non branché")


def test_lpr_en_erreur_ne_tue_pas_la_boucle():
    """Une caméra d'entrée avec un LPR non implémenté ne doit pas crasher :
    on émet ENTREE + une PLAQUE vide plutôt que de propager l'exception."""
    cfg = {"id": "cam_entree", "role": "entree",
           "ligne_entree": [[0, 100], [200, 100]]}
    vehicule_haut = SimpleNamespace(track_id="v1", bbox=(50, 0, 90, 40), classe="car")
    vehicule_bas = SimpleNamespace(track_id="v1", bbox=(50, 150, 90, 190), classe="car")
    client = FakeClient()
    worker = CameraWorker(cfg, detector=FakeDetector([]),
                          tracker=FakeTracker([vehicule_haut]), client=client,
                          lpr=_LPRQuiCasse())
    worker.traiter_frame(object())                 # 1er côté de la ligne
    worker.tracker = FakeTracker([vehicule_bas])
    worker.traiter_frame(object())                 # franchissement -> ENTREE + PLAQUE

    types = [e.type for e in client.events]
    assert EventType.ENTREE in types
    assert EventType.PLAQUE in types               # émise malgré l'échec OCR
    plaque = next(e for e in client.events if e.type == EventType.PLAQUE)
    assert plaque.plaque is None                   # pas de valeur (saisie manuelle)


def test_gilet_desactive_pas_de_detection(monkeypatch):
    monkeypatch.setattr(orch, "couleur_dominante", lambda img, bbox: (220, 35, 70))
    cfg = {**CONFIG_ZONE, "detecter_gilet": False}
    vehicule = SimpleNamespace(track_id="v1", bbox=(100, 100, 200, 200), classe="car")
    laveur = SimpleNamespace(bbox=(150, 150, 190, 260), confiance=0.8, classe="person")
    worker = CameraWorker(
        cfg, detector=FakeDetector([laveur]),
        tracker=FakeTracker([vehicule]), client=(client := FakeClient()),
    )
    worker.traiter_frame(image=object())
    assert all(e.type != EventType.BADGE for e in client.events)
