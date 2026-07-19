"""★ CŒUR MÉTIER — Classification du forfait réellement effectué.

Combine deux approches (cf. section 7 du cahier des charges) :
  1. Zones visitées : quelles étapes (B lavage, C aspiration, D polish) ont eu lieu.
  2. Durée : temps total et temps par zone, comparés aux seuils du forfait.

La logique déterministe ci-dessous est volontairement complète car entièrement
spécifiée. L'évolution "phase 2" (classification vidéo des gestes par IA) viendra
enrichir `forfait_detecte` — voir TODO(dev) en bas de fichier.
"""
from dataclasses import dataclass

from app.models.enums import ForfaitNom, ZoneCode

# Parcours de zones attendu par forfait (source: tableau 7.1).
# Ordonné du plus complet au plus simple pour la déduction.
FORFAIT_ZONES: dict[ForfaitNom, set[str]] = {
    ForfaitNom.COMPLET: {ZoneCode.LAVAGE_EXT.value, ZoneCode.ASPIRATION.value, ZoneCode.POLISH.value},
    ForfaitNom.PREMIUM: {ZoneCode.LAVAGE_EXT.value, ZoneCode.ASPIRATION.value},
    ForfaitNom.RAPIDE: {ZoneCode.LAVAGE_EXT.value},
}


@dataclass
class ParcoursVehicule:
    """Résumé du passage d'un véhicule, extrait de la transaction."""
    zones_visitees: set[str]      # ex: {"B", "C"}
    duree_totale_min: float | None  # minutes


def deduire_forfait_effectue(parcours: ParcoursVehicule) -> ForfaitNom:
    """Déduit le forfait qui correspond le mieux aux zones réellement visitées.

    Règle : on retient le forfait le plus élevé dont TOUTES les zones requises
    ont été couvertes.
    """
    for forfait in (ForfaitNom.COMPLET, ForfaitNom.PREMIUM, ForfaitNom.RAPIDE):
        if FORFAIT_ZONES[forfait].issubset(parcours.zones_visitees):
            return forfait
    # Aucune zone de lavage détectée : on retombe sur Rapide par défaut.
    return ForfaitNom.RAPIDE


def est_conforme(forfait_paye: ForfaitNom, parcours: ParcoursVehicule,
                 temps_min_paye: int) -> bool:
    """Le lavage effectué respecte-t-il le forfait payé ?

    Conforme si :
      - toutes les zones requises par le forfait payé ont été visitées, ET
      - la durée totale atteint le temps minimum attendu du forfait payé.
    """
    zones_ok = FORFAIT_ZONES[forfait_paye].issubset(parcours.zones_visitees)
    temps_ok = (
        parcours.duree_totale_min is None
        or parcours.duree_totale_min >= temps_min_paye
    )
    return zones_ok and temps_ok


# TODO(dev): phase 2 — classification vidéo des gestes (lavage/aspiration/cirage)
#   pour confirmer visuellement l'étape au lieu de la seule présence en zone.
#   Entraîner un modèle d'action-recognition sur des clips annotés, l'exécuter
#   dans `ai/`, et transmettre le résultat via EventIn.meta pour affiner ici.
