"""Détection + suivi + comptage de véhicules sur un FICHIER VIDÉO (sans caméras).

Utilise YOLO + ByteTrack (via ultralytics) pour un comptage FIABLE (chaque
véhicule compté une seule fois grâce au track_id). Peut aussi émettre des
événements ENTREE/SORTIE vers le backend, comme le ferait une vraie caméra.

Prérequis : pip install ultralytics opencv-python

Exemples :
    python detect_video.py --video lavage.mp4 --ligne 0,540,1920,540 --out annote.mp4
    python detect_video.py --video lavage.mp4 --ligne 0,540,1920,540 --emit \
        --backend http://localhost:8000 --ingest-key change-me-ingest-key
"""
from __future__ import annotations

import argparse
import os

from pipeline.events import Event, EventClient, EventType
from pipeline.tracker import Tracker
from pipeline.zones import DetecteurLigne


def _point_reference(bbox) -> tuple[float, float]:
    x1, y1, x2, y2 = bbox
    return ((x1 + x2) / 2, y2)  # centre du bas


def _dessiner(image, tracks, compteur):
    import cv2
    for t in tracks:
        x1, y1, x2, y2 = map(int, t.bbox)
        cv2.rectangle(image, (x1, y1), (x2, y2), (0, 200, 0), 2)
        cv2.putText(image, f"#{t.track_id} {t.classe}", (x1, y1 - 6),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 200, 0), 1)
    cv2.putText(image, f"Comptage: {compteur}", (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2)
    return image


def main() -> None:
    parser = argparse.ArgumentParser(description="Détection + suivi de véhicules sur vidéo")
    parser.add_argument("--video", required=True)
    parser.add_argument("--weights", default="yolov8n.pt")
    parser.add_argument("--conf", type=float, default=0.4)
    parser.add_argument("--ligne", default=None, help="Ligne de comptage x1,y1,x2,y2")
    parser.add_argument("--out", default=None, help="Vidéo annotée de sortie (mp4)")
    parser.add_argument("--show", action="store_true")
    # Émission d'événements vers le backend (comme une vraie caméra).
    parser.add_argument("--emit", action="store_true")
    parser.add_argument("--backend", default="http://localhost:8000")
    parser.add_argument("--ingest-key", default=os.getenv("AI_INGEST_API_KEY", ""))
    args = parser.parse_args()

    import cv2

    tracker = Tracker(args.weights, conf=args.conf)
    tracker.load()

    ligne = None
    if args.ligne:
        x1, y1, x2, y2 = (float(v) for v in args.ligne.split(","))
        ligne = DetecteurLigne((x1, y1), (x2, y2))

    client = None
    if args.emit:
        client = EventClient(f"{args.backend}/api/v1/events", args.ingest_key)

    cap = cv2.VideoCapture(args.video)
    if not cap.isOpened():
        raise SystemExit(f"Impossible d'ouvrir : {args.video}")

    writer = None
    if args.out:
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS) or 25
        writer = cv2.VideoWriter(args.out, cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))

    compteur = 0
    comptes = set()  # track_ids déjà comptés (anti-doublon)
    idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        tracks = tracker.update(frame)
        if ligne:
            for t in tracks:
                if ligne.a_franchi(t.track_id, _point_reference(t.bbox)) \
                        and t.track_id not in comptes:
                    comptes.add(t.track_id)
                    compteur += 1
                    if client:
                        client.send(Event(EventType.ENTREE, track_id=t.track_id,
                                          camera_id="video_test"))
        frame = _dessiner(frame, tracks, compteur)
        if writer:
            writer.write(frame)
        if args.show:
            cv2.imshow("detection", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
        idx += 1

    cap.release()
    if writer:
        writer.release()
    print(f"Terminé : {idx} images, {compteur} véhicule(s) compté(s). "
          f"Sortie : {args.out or '(aucune)'}")


if __name__ == "__main__":
    main()
