"""Génération du rapport journalier (agrégats + PDF) et planification.

Chaque soir (settings.report_daily_hour), un job APScheduler appelle
`generer_rapport_journalier`. Le rapport agrège les transactions du jour,
calcule les KPI et la performance par employé, génère un PDF (ReportLab) et
l'envoie (WhatsApp/email).

SQUELETTE : les agrégats SQL et la mise en page PDF sont à finir.
"""
from datetime import date

from sqlalchemy.orm import Session

from app.models import RapportJournalier


def generer_rapport_journalier(db: Session, jour: date) -> RapportJournalier:
    """Construit (ou met à jour) le rapport du jour donné."""
    stats = _agreger_journee(db, jour)

    rapport = RapportJournalier(
        date=jour,
        total_vehicules=stats["total_vehicules"],
        total_ca=stats["total_ca"],
        repartition_forfaits=stats["repartition_forfaits"],
        taux_conformite=stats["taux_conformite"],
        nombre_anomalies=stats["nombre_anomalies"],
        performance_employes=stats["performance_employes"],
    )
    # TODO(dev): upsert (remplacer si un rapport existe déjà pour ce jour).
    db.add(rapport)
    db.flush()

    rapport.fichier_pdf = _generer_pdf(rapport)
    db.commit()
    return rapport


def _agreger_journee(db: Session, jour: date) -> dict:
    """Calcule les KPI de la journée à partir des transactions clôturées.

    TODO(dev): écrire les requêtes SQL d'agrégation :
      - total_vehicules   : COUNT(transactions cloturées du jour)
      - total_ca          : SUM(forfait.prix) des transactions facturées
      - repartition_forfaits : GROUP BY forfait_detecte
      - taux_conformite   : conformes / total * 100
      - nombre_anomalies  : COUNT(anomalies du jour)
      - performance_employes : par employé -> vehicules/jour, temps moyen,
                               taux conformité, revenus, score qualité (cf. 8.2)
    """
    return {
        "total_vehicules": 0,
        "total_ca": 0.0,
        "repartition_forfaits": {},
        "taux_conformite": 0.0,
        "nombre_anomalies": 0,
        "performance_employes": [],
    }


def _generer_pdf(rapport: RapportJournalier) -> str:
    """Génère le PDF du rapport et retourne son chemin.

    TODO(dev): mise en page ReportLab (résumé du jour, graphique horaire,
    tableau employés, liste des anomalies avec photos, comparaisons vs veille /
    semaine précédente / moyenne mensuelle).
    """
    # placeholder : retourne un chemin fictif tant que non implémenté
    return f"reports/rapport_{rapport.date.isoformat()}.pdf"
