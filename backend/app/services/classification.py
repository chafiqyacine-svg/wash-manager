"""★ CŒUR MÉTIER — Classification du forfait réellement effectué.

Piloté par la BASE (et non par une liste figée) : n'importe quel forfait défini
par ses zones requises / prix / temps fonctionne, y compris les services ajoutés
par le gérant depuis l'écran Configuration.

Combine deux approches (cf. section 7 du cahier des charges) :
  1. Zones visitées : quelles étapes (B lavage, C aspiration, D polish) ont eu lieu.
  2. Durée : temps total comparé au temps minimum du forfait.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class ForfaitDef:
    """Définition d'un forfait, découplée de l'ORM (utilisable en logique pure)."""
    nom: str
    zones_requises: frozenset[str]   # ex: frozenset({"B", "C", "D"})
    temps_min: int                   # minutes
    prix: float


def rang(forfait: ForfaitDef) -> tuple[int, float]:
    """Ordre de « richesse » d'un forfait : plus de zones, puis prix plus élevé."""
    return (len(forfait.zones_requises), forfait.prix)


def deduire_forfait_effectue(
    zones_visitees: set[str], forfaits: list[ForfaitDef]
) -> ForfaitDef | None:
    """Retourne le forfait le plus « riche » dont TOUTES les zones requises ont
    été visitées. None si aucun forfait ne correspond (ex: aucune zone détectée).
    """
    candidats = [f for f in forfaits if f.zones_requises <= zones_visitees]
    if not candidats:
        return None
    return max(candidats, key=rang)


def est_conforme(
    forfait_paye: ForfaitDef, zones_visitees: set[str], duree_totale_min: float | None
) -> bool:
    """Le lavage effectué respecte-t-il le forfait payé ?

    Conforme si toutes les zones requises ont été visitées ET la durée atteint le
    temps minimum attendu du forfait payé.
    """
    zones_ok = forfait_paye.zones_requises <= zones_visitees
    temps_ok = duree_totale_min is None or duree_totale_min >= forfait_paye.temps_min
    return zones_ok and temps_ok


# TODO(dev): phase 2 — classification vidéo des gestes (lavage/aspiration/cirage)
#   pour confirmer visuellement l'étape au lieu de la seule présence en zone.
