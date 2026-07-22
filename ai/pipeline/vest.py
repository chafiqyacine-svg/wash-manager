"""Reconnaissance de gilet — identifie l'employé par la couleur de son gilet.

Deux parties :
  1. `couleur_dominante` : extrait la couleur moyenne de la région torse d'une
     personne détectée (nécessite numpy/OpenCV) — à appeler avec le crop du torse.
  2. matching couleur → gilet enregistré (fonctions PURES, testées) :
     - `snap_couleur` : ramène une couleur mesurée (bruitée) à la couleur de
       référence enregistrée la plus proche. C'est cette couleur canonique qui
       est envoyée au backend (`EventIn.couleur_gilet`), car le backend fait un
       rapprochement EXACT (`Employe.couleur_gilet == event.couleur_gilet`) : le
       edge absorbe donc le bruit de mesure, le backend reste déterministe.
     - `plus_proche_employe` : variante renvoyant directement l'employe_id (utile
       si l'on connaît la palette {employe_id: couleur} côté edge).

Approche simple et robuste au lancement. TODO(dev) : passer en espace HSV/LAB et
gérer l'éclairage variable pour plus de robustesse.
"""
from __future__ import annotations


def hex_vers_rgb(hex_couleur: str) -> tuple[int, int, int]:
    h = hex_couleur.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def rgb_vers_hex(rgb: tuple[int, int, int]) -> str:
    return "#{:02X}{:02X}{:02X}".format(*(max(0, min(255, int(c))) for c in rgb))


def distance2(a: tuple[int, int, int], b: tuple[int, int, int]) -> int:
    """Distance euclidienne au carré entre deux couleurs RGB."""
    return sum((x - y) ** 2 for x, y in zip(a, b))


def plus_proche_employe(
    rgb: tuple[int, int, int],
    palette: dict[int, str],
    seuil: int = 6000,
) -> int | None:
    """Retourne l'employe_id dont la couleur de gilet est la plus proche de `rgb`.

    `palette` : {employe_id: "#RRGGBB"}. Retourne None si aucune couleur n'est
    assez proche (distance² > seuil) pour éviter les fausses associations.
    """
    meilleur_id = None
    meilleure_dist = None
    for employe_id, hex_couleur in palette.items():
        if not hex_couleur:
            continue
        d = distance2(rgb, hex_vers_rgb(hex_couleur))
        if meilleure_dist is None or d < meilleure_dist:
            meilleure_dist, meilleur_id = d, employe_id
    if meilleure_dist is None or meilleure_dist > seuil:
        return None
    return meilleur_id


def snap_couleur(
    rgb: tuple[int, int, int],
    couleurs_ref: list[str],
    seuil: int = 6000,
) -> str | None:
    """Ramène `rgb` à la couleur de référence enregistrée la plus proche.

    `couleurs_ref` : liste de "#RRGGBB" (gilets enregistrés des employés).
    Retourne le hex canonique le plus proche, ou None si aucun sous le seuil
    (distance²) — évite d'attribuer un gilet inconnu à un employé.
    """
    meilleur = None
    meilleure_dist = None
    for hex_couleur in couleurs_ref:
        if not hex_couleur:
            continue
        d = distance2(rgb, hex_vers_rgb(hex_couleur))
        if meilleure_dist is None or d < meilleure_dist:
            meilleure_dist, meilleur = d, hex_couleur
    if meilleure_dist is None or meilleure_dist > seuil:
        return None
    return meilleur


def bbox_la_plus_proche(
    point: tuple[float, float],
    bboxes: list[tuple[float, float, float, float]],
) -> int | None:
    """Index de la bbox dont le centre est le plus proche de `point`.

    Sert à attribuer au véhicule (dans une zone) le laveur qui s'en occupe :
    la personne la plus proche du point de référence du véhicule. None si vide.
    """
    meilleur_idx = None
    meilleure_dist = None
    px, py = point
    for i, (x1, y1, x2, y2) in enumerate(bboxes):
        cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
        d = (cx - px) ** 2 + (cy - py) ** 2
        if meilleure_dist is None or d < meilleure_dist:
            meilleure_dist, meilleur_idx = d, i
    return meilleur_idx


def couleur_dominante(image, bbox: tuple[float, float, float, float]) -> tuple[int, int, int]:
    """Couleur moyenne de la région « torse » d'une personne (tiers supérieur du
    corps). `image` = frame BGR (OpenCV), `bbox` = (x1,y1,x2,y2) de la personne.
    """
    import numpy as np

    x1, y1, x2, y2 = (int(v) for v in bbox)
    h = y2 - y1
    # Zone torse : ~20%–55% de la hauteur, centrée horizontalement.
    ty1, ty2 = y1 + int(0.20 * h), y1 + int(0.55 * h)
    tx1, tx2 = x1 + int(0.25 * (x2 - x1)), x2 - int(0.25 * (x2 - x1))
    crop = image[ty1:ty2, tx1:tx2]
    if crop.size == 0:
        return (0, 0, 0)
    moyenne = crop.reshape(-1, 3).mean(axis=0)  # BGR
    b, g, r = moyenne
    return (int(r), int(g), int(b))
