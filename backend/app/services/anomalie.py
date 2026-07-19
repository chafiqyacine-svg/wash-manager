"""★ Règles de détection d'anomalies (cf. sections 7.2 et 9.2).

`detecter_anomalies` est appelé à la clôture d'une transaction (et pour les cas
POS sans véhicule / véhicule sans POS depuis le service d'ingestion). Il retourne
une liste d'anomalies à persister ; l'envoi des alertes est géré séparément par
services/notification.py.
"""
from dataclasses import dataclass

from app.models.enums import AnomalieSeverite, AnomalieType, ForfaitNom, ZoneCode
from app.services.classification import FORFAIT_ZONES


@dataclass
class AnomalieDetectee:
    type: AnomalieType
    severite: AnomalieSeverite
    description: str


@dataclass
class ContexteTransaction:
    """Données nécessaires à l'évaluation des règles."""
    forfait_paye: ForfaitNom | None       # None => pas de ticket POS
    forfait_detecte: ForfaitNom | None    # None => aucun véhicule détecté
    zones_visitees: set[str]
    duree_totale_min: float | None
    plaque_lue: bool


# Ordre de "richesse" des forfaits pour comparer payé vs effectué.
_RANG = {ForfaitNom.RAPIDE: 1, ForfaitNom.PREMIUM: 2, ForfaitNom.COMPLET: 3}


def detecter_anomalies(ctx: ContexteTransaction) -> list[AnomalieDetectee]:
    anomalies: list[AnomalieDetectee] = []

    # 1) Véhicule sans ticket POS -> lavage non facturé
    if ctx.forfait_paye is None and ctx.forfait_detecte is not None:
        anomalies.append(AnomalieDetectee(
            AnomalieType.LAVAGE_NON_FACTURE, AnomalieSeverite.HAUTE,
            "Véhicule lavé sans ticket POS associé.",
        ))
        return anomalies  # rien d'autre à comparer

    # 2) Ticket POS sans véhicule détecté -> ticket fantôme
    if ctx.forfait_paye is not None and ctx.forfait_detecte is None:
        anomalies.append(AnomalieDetectee(
            AnomalieType.TICKET_FANTOME, AnomalieSeverite.HAUTE,
            "Ticket POS sans véhicule détecté sur le site.",
        ))
        return anomalies

    if ctx.forfait_paye is not None and ctx.forfait_detecte is not None:
        # 3) Forfait payé supérieur au forfait effectué -> non respecté
        if _RANG[ctx.forfait_detecte] < _RANG[ctx.forfait_paye]:
            anomalies.append(AnomalieDetectee(
                AnomalieType.FORFAIT_NON_RESPECTE, AnomalieSeverite.CRITIQUE,
                f"Forfait {ctx.forfait_paye.value} payé mais seul "
                f"{ctx.forfait_detecte.value} effectué.",
            ))

        # 4) Zone requise manquée (ex: aspiration absente pour Premium)
        zones_manquantes = FORFAIT_ZONES[ctx.forfait_paye] - ctx.zones_visitees
        if zones_manquantes:
            libelle = ", ".join(sorted(_nom_zone(z) for z in zones_manquantes))
            anomalies.append(AnomalieDetectee(
                AnomalieType.FORFAIT_NON_RESPECTE, AnomalieSeverite.CRITIQUE,
                f"Étape(s) manquante(s) pour {ctx.forfait_paye.value} : {libelle}.",
            ))

        # 5) Durée anormalement courte au regard du forfait payé
        seuils_min = {ForfaitNom.COMPLET: 10, ForfaitNom.PREMIUM: 20}
        seuil = seuils_min.get(ctx.forfait_paye)
        if (seuil is not None and ctx.duree_totale_min is not None
                and ctx.duree_totale_min < seuil):
            anomalies.append(AnomalieDetectee(
                AnomalieType.TEMPS_ANORMAL, AnomalieSeverite.MOYENNE,
                f"Durée {ctx.duree_totale_min:.0f} min trop courte pour "
                f"{ctx.forfait_paye.value} (< {seuil} min).",
            ))

    # 6) Plaque non lue par l'OCR
    if not ctx.plaque_lue:
        anomalies.append(AnomalieDetectee(
            AnomalieType.PLAQUE_NON_LUE, AnomalieSeverite.BASSE,
            "Échec de lecture de plaque — capture stockée pour saisie manuelle.",
        ))

    return anomalies


def _nom_zone(code: str) -> str:
    return {
        ZoneCode.LAVAGE_EXT.value: "lavage extérieur",
        ZoneCode.ASPIRATION.value: "aspiration",
        ZoneCode.POLISH.value: "polish/cire",
    }.get(code, code)
