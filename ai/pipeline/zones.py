"""Zones & lignes virtuelles : détection de franchissement et de présence.

La géométrie (côté d'une ligne, point-dans-polygone) est implémentée ici car
purement déterministe. Ce qui reste à finir (TODO(dev)) : choisir le point de
référence de la bbox (ex: centre du bas) et régler l'hystérésis pour éviter les
détections parasites.
"""
from __future__ import annotations

Point = tuple[float, float]

# Nombre max de track_id mémorisés par détecteur : borne la mémoire sur les
# longues sessions (le tracker crée sans cesse de nouveaux id).
MAX_TRACKS = 4096


def _borner(etat: dict, maximum: int = MAX_TRACKS) -> None:
    """Évince les plus anciens track_id tant que `etat` dépasse `maximum`.
    (Les dicts Python conservent l'ordre d'insertion → le 1er est le plus vieux.)"""
    while len(etat) > maximum:
        etat.pop(next(iter(etat)))


def _cote_ligne(p: Point, a: Point, b: Point) -> float:
    """Signe indiquant de quel côté de la ligne (a→b) se trouve p."""
    return (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])


class DetecteurLigne:
    """Détecte le franchissement d'une ligne virtuelle par un track donné.

    Mémorise le dernier côté *défini* de chaque track ; un changement de côté =
    franchissement. Deux garde-fous contre les faux positifs :

    - `marge` : bande morte (en unités de `_cote_ligne`) autour de la ligne. Un
      point trop proche est « indéterminé » : on ne met pas à jour le côté, ce
      qui évite le clignotement quand un véhicule stationne pile sur la ligne.
    - `sens` : 0 = tout franchissement ; +1 = ne compter que le passage
      côté négatif → positif ; -1 = l'inverse. Utile pour ne pas compter une
      entrée quand un véhicule fait marche arrière au-dessus de la ligne
      (le sens dépend de la calibration a→b, cf. config).
    """

    def __init__(self, a: Point, b: Point, max_tracks: int = MAX_TRACKS,
                 marge: float = 0.0, sens: int = 0) -> None:
        self.a = a
        self.b = b
        self.max_tracks = max_tracks
        self.marge = marge
        self.sens = sens
        self._dernier_cote: dict[str, int] = {}   # dernier côté DÉFINI : -1 / +1

    def a_franchi(self, track_id: str, point: Point) -> bool:
        cote = _cote_ligne(point, self.a, self.b)
        if abs(cote) < self.marge:
            return False  # dans la bande morte : côté indéterminé, aucun changement
        signe = 1 if cote > 0 else -1
        precedent = self._dernier_cote.get(track_id)
        self._dernier_cote[track_id] = signe
        _borner(self._dernier_cote, self.max_tracks)
        if precedent is None or precedent == signe:
            return False
        if self.sens == 0:
            return True
        # Ne compter que le sens demandé (precedent → signe).
        return (self.sens > 0 and signe > 0) or (self.sens < 0 and signe < 0)


def point_dans_polygone(point: Point, polygone: list[Point]) -> bool:
    """Ray casting : True si le point est à l'intérieur du polygone."""
    x, y = point
    dedans = False
    n = len(polygone)
    j = n - 1
    for i in range(n):
        xi, yi = polygone[i]
        xj, yj = polygone[j]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi + 1e-12) + xi):
            dedans = not dedans
        j = i
    return dedans


class DetecteurZone:
    """Suit l'entrée/sortie d'une zone (polygone) pour chaque track.

    Retourne un événement "enter" ou "exit" au changement d'état, sinon None.

    `confirmations` : nombre de frames consécutives où l'état candidat doit
    persister avant de basculer (anti-rebond). 1 = bascule immédiate (défaut) ;
    >1 filtre les clignotements aux bords du polygone.
    """

    def __init__(self, polygone: list[Point], max_tracks: int = MAX_TRACKS,
                 confirmations: int = 1) -> None:
        self.polygone = polygone
        self.max_tracks = max_tracks
        self.confirmations = max(1, confirmations)
        self._present: dict[str, bool] = {}   # état confirmé
        self._compte: dict[str, int] = {}      # frames consécutives de l'état candidat

    def maj(self, track_id: str, point: Point) -> str | None:
        dedans = point_dans_polygone(point, self.polygone)
        avant = self._present.get(track_id, False)
        if dedans == avant:
            self._compte[track_id] = 0        # l'état candidat rejoint l'état confirmé
            return None
        # L'état candidat diffère : il doit persister `confirmations` frames.
        compte = self._compte.get(track_id, 0) + 1
        if compte < self.confirmations:
            self._compte[track_id] = compte
            return None
        self._present[track_id] = dedans
        self._compte[track_id] = 0
        _borner(self._present, self.max_tracks)
        _borner(self._compte, self.max_tracks)
        return "enter" if dedans else "exit"
