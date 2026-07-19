"""★ Règles de détection d'anomalies (cf. sections 7.2 et 9.2).

Piloté par la base (ForfaitDef) : compatible avec les services ajoutés par le
gérant. Appelé à la finalisation d'une transaction. Retourne une liste
d'anomalies à persister ; l'envoi des alertes est géré par notification.py.
"""
from dataclasses import dataclass

from app.models.enums import AnomalieSeverite, AnomalieType, ZoneCode
from app.services.classification import ForfaitDef, rang


@dataclass
class AnomalieDetectee:
    type: AnomalieType
    severite: AnomalieSeverite
    description: str


@dataclass
class ContexteTransaction:
    """Données nécessaires à l'évaluation des règles."""
    forfait_paye: ForfaitDef | None       # None => pas de ticket POS
    forfait_detecte: ForfaitDef | None    # None => aucun véhicule détecté
    zones_visitees: set[str]
    duree_totale_min: float | None
    plaque_lue: bool


def detecter_anomalies(ctx: ContexteTransaction) -> list[AnomalieDetectee]:
    anomalies: list[AnomalieDetectee] = []

    # 1) Véhicule sans ticket POS -> lavage non facturé
    if ctx.forfait_paye is None and ctx.forfait_detecte is not None:
        anomalies.append(AnomalieDetectee(
            AnomalieType.LAVAGE_NON_FACTURE, AnomalieSeverite.HAUTE,
            "Véhicule lavé sans ticket POS associé.",
        ))
        return anomalies

    # 2) Ticket POS sans véhicule détecté -> ticket fantôme
    if ctx.forfait_paye is not None and ctx.forfait_detecte is None:
        anomalies.append(AnomalieDetectee(
            AnomalieType.TICKET_FANTOME, AnomalieSeverite.HAUTE,
            "Ticket POS sans véhicule détecté sur le site.",
        ))
        return anomalies

    if ctx.forfait_paye is not None and ctx.forfait_detecte is not None:
        # 3) Forfait payé plus « riche » que le forfait effectué -> non respecté
        if rang(ctx.forfait_detecte) < rang(ctx.forfait_paye):
            anomalies.append(AnomalieDetectee(
                AnomalieType.FORFAIT_NON_RESPECTE, AnomalieSeverite.CRITIQUE,
                f"Forfait {ctx.forfait_paye.nom} payé mais seul "
                f"{ctx.forfait_detecte.nom} effectué.",
            ))

        # 4) Zone requise manquée (ex: aspiration absente pour Premium)
        zones_manquantes = ctx.forfait_paye.zones_requises - ctx.zones_visitees
        if zones_manquantes:
            libelle = ", ".join(sorted(_nom_zone(z) for z in zones_manquantes))
            anomalies.append(AnomalieDetectee(
                AnomalieType.FORFAIT_NON_RESPECTE, AnomalieSeverite.CRITIQUE,
                f"Étape(s) manquante(s) pour {ctx.forfait_paye.nom} : {libelle}.",
            ))

        # 5) Durée anormalement courte au regard du temps minimum du forfait payé
        if (ctx.duree_totale_min is not None
                and ctx.duree_totale_min < ctx.forfait_paye.temps_min):
            anomalies.append(AnomalieDetectee(
                AnomalieType.TEMPS_ANORMAL, AnomalieSeverite.MOYENNE,
                f"Durée {ctx.duree_totale_min:.0f} min trop courte pour "
                f"{ctx.forfait_paye.nom} (< {ctx.forfait_paye.temps_min} min).",
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
