"""Lanceur du pipeline edge.

Usage : python run.py --config config.yaml

Charge la config, instancie les modèles et un worker par caméra, puis lance les
boucles de lecture (un thread par caméra recommandé).

SQUELETTE : le câblage des threads/boucles de frames est marqué TODO(dev).
"""
from __future__ import annotations

import argparse
import os

import yaml

from pipeline.detector import Detector
from pipeline.events import EventClient
from pipeline.lpr import LecteurPlaque
from pipeline.orchestrator import CameraWorker
from pipeline.tracker import Tracker


def charger_config(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def injecter_palette(cameras: list[dict], palette: list[str]) -> None:
    """Renseigne `palette_gilets` des caméras zone qui n'en figent pas une.

    Une palette figée en config a priorité (override) ; sinon on utilise celle
    chargée depuis le backend. Modifie `cameras` en place.
    """
    for cam in cameras:
        if cam.get("detecter_gilet") and not cam.get("palette_gilets"):
            cam["palette_gilets"] = list(palette)


def main() -> None:
    parser = argparse.ArgumentParser(description="Pipeline IA lavage auto (edge)")
    parser.add_argument("--config", default="config.yaml")
    args = parser.parse_args()

    cfg = charger_config(args.config)

    # Client backend
    api_key = os.getenv(cfg["backend"].get("api_key_env", "AI_INGEST_API_KEY"), "")
    client = EventClient(cfg["backend"]["events_url"], api_key)

    # Palette de gilets : chargée dynamiquement depuis le backend (source de
    # vérité = employés enregistrés), sauf si la caméra en fige une en config.
    palette_backend = client.charger_palette_gilets()
    injecter_palette(cfg["cameras"], palette_backend)
    print(f"Palette gilets chargée depuis le backend : {len(palette_backend)} couleur(s).")

    # Modèles partagés (TODO(dev): .load() réel — nécessite les poids)
    detector = Detector(cfg["models"]["vehicule_detector"])
    # Le tracker détecte + suit les véhicules en une passe (ByteTrack).
    tracker = Tracker(cfg["models"]["vehicule_detector"],
                      tracker_cfg=f"{cfg['tracking']['type']}.yaml")
    plaque_detector = Detector(cfg["models"]["plaque_detector"])
    lpr = LecteurPlaque(plaque_detector, cfg["models"]["ocr_lang"])
    # detector.load(); tracker.load(); plaque_detector.load(); lpr.load()

    # Un worker par caméra
    workers = [
        CameraWorker(cam, detector, tracker, client,
                     lpr=lpr if cam["role"] == "entree" else None)
        for cam in cfg["cameras"]
    ]

    # TODO(dev): pour chaque worker, ouvrir CameraStream(cam.source) et lancer
    #   un thread qui appelle worker.traiter_frame(frame.image) sur chaque frame.
    #   Gérer l'arrêt propre (SIGINT) et la supervision des threads.
    print(f"{len(workers)} worker(s) caméra initialisé(s). "
          f"Brancher les boucles de frames (TODO(dev)).")


if __name__ == "__main__":
    main()
