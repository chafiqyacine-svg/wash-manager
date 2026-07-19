"""Test de détection de véhicules sur un FICHIER VIDÉO (sans caméras installées).

Charge YOLO (poids COCO pré-entraînés `yolov8n.pt` par défaut — téléchargés
automatiquement au premier lancement), détecte les véhicules image par image,
compte les franchissements d'une ligne virtuelle et écrit une vidéo annotée.

Prérequis : pip install ultralytics opencv-python

Exemples :
    python detect_video.py --video lavage.mp4
    python detect_video.py --video lavage.mp4 --ligne 0,540,1920,540 --out annote.mp4

Le compteur de ligne permet de valider le comptage d'entrées/sorties avant
d'installer les vraies caméras.
"""
from __future__ import annotations

import argparse

from pipeline.detector import Detector
from pipeline.zones import DetecteurLigne


def _dessiner(image, detections, compteur):
    import cv2
    for d in detections:
        x1, y1, x2, y2 = map(int, d.bbox)
        cv2.rectangle(image, (x1, y1), (x2, y2), (0, 200, 0), 2)
        cv2.putText(image, f"{d.classe} {d.confiance:.2f}", (x1, y1 - 6),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 200, 0), 1)
    cv2.putText(image, f"Comptage: {compteur}", (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2)
    return image


def main() -> None:
    parser = argparse.ArgumentParser(description="Détection de véhicules sur vidéo")
    parser.add_argument("--video", required=True, help="Chemin du fichier vidéo")
    parser.add_argument("--weights", default="yolov8n.pt", help="Poids YOLO")
    parser.add_argument("--conf", type=float, default=0.4)
    parser.add_argument("--ligne", default=None,
                        help="Ligne de comptage x1,y1,x2,y2 (pixels)")
    parser.add_argument("--out", default=None, help="Vidéo annotée de sortie (mp4)")
    parser.add_argument("--show", action="store_true", help="Afficher la fenêtre")
    args = parser.parse_args()

    import cv2

    detector = Detector(args.weights, conf=args.conf)
    detector.load()

    ligne = None
    if args.ligne:
        x1, y1, x2, y2 = (float(v) for v in args.ligne.split(","))
        ligne = DetecteurLigne((x1, y1), (x2, y2))

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
    idx = 0
    # Compteur simplifié par centre de bbox (sans tracker : approximation de test).
    # TODO(dev): brancher le tracker pour un comptage exact sans doublons.
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        detections = detector.detect_vehicules(frame)
        if ligne:
            for i, d in enumerate(detections):
                cx = (d.bbox[0] + d.bbox[2]) / 2
                cy = d.bbox[3]  # bas de la bbox
                if ligne.a_franchi(f"{idx}-{i}", (cx, cy)):
                    compteur += 1
        frame = _dessiner(frame, detections, compteur)
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
    print(f"Terminé : {idx} images traitées. Sortie : {args.out or '(aucune)'}")


if __name__ == "__main__":
    main()
