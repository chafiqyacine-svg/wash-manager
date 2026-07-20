"""Reconnaissance de gilet — identifie l'employé par la couleur de son gilet.

Deux parties :
  1. `couleur_dominante` : extrait la couleur moyenne de la région torse d'une
     personne détectée (nécessite numpy/OpenCV) — à appeler avec le crop du torse.
  2. `plus_proche_employe` : associe une couleur à l'employé dont le gilet est le
     plus proche (fonction PURE, testée). C'est la couleur envoyée au backend
     (EventIn.couleur_gilet), qui la rapproche ensuite de l'employé.

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
