"""Objectifs de pilotage : calcul des valeurs réelles du jour et écarts.

Pour chaque objectif configuré (par site), on compare la valeur réelle du jour
à la cible et on indique si elle est atteinte + l'écart. Réutilise la clôture
pour le CA (recettes réelles) et les transactions pour la conformité.
"""
from datetime import date, datetime, time, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Bay, Objectif, Transaction
from app.services.cloture import calculer_cloture

# Métriques supportées : libellé, unité, sens par défaut (min = plancher).
METRIQUES = {
    "ca_journalier": {"label": "CA journalier", "unite": "DH", "sens": "min"},
    "taux_conformite": {"label": "Taux de conformité", "unite": "%", "sens": "min"},
    "lavages_non_factures": {"label": "Lavages non facturés", "unite": "", "sens": "max"},
    "vehicules": {"label": "Véhicules traités", "unite": "", "sens": "min"},
}


def _actuals(db: Session, jour: date, site_id: int | None) -> dict[str, float]:
    """Valeurs réelles du jour pour un site (ou tous si site_id None)."""
    debut = datetime.combine(jour, time.min)
    fin = debut + timedelta(days=1)

    stmt = select(Transaction).where(
        Transaction.statut == "cloturee",
        Transaction.heure_sortie >= debut,
        Transaction.heure_sortie < fin,
    )
    if site_id:
        bay_ids = list(db.scalars(select(Bay.id).where(Bay.site_id == site_id)).all())
        stmt = stmt.where(Transaction.bay_id.in_(bay_ids))
    txns = db.scalars(stmt).all()

    evaluees = [t for t in txns if t.conforme is not None]
    conformes = sum(1 for t in evaluees if t.conforme)
    taux = round(conformes / len(evaluees) * 100, 1) if evaluees else 100.0
    non_factures = sum(1 for t in txns if t.forfait_id is None)

    ca = calculer_cloture(db, jour, site_id)["total_theorique"]

    return {
        "ca_journalier": round(ca, 2),
        "taux_conformite": taux,
        "lavages_non_factures": non_factures,
        "vehicules": len(txns),
    }


def evaluer(db: Session, jour: date, site_id: int | None) -> list[dict]:
    """Compare chaque objectif (du même périmètre) à la valeur réelle du jour."""
    actuals = _actuals(db, jour, site_id)

    stmt = select(Objectif).where(Objectif.actif.is_(True))
    stmt = stmt.where(Objectif.site_id == site_id) if site_id \
        else stmt.where(Objectif.site_id.is_(None))
    objectifs = db.scalars(stmt).all()

    lignes = []
    for o in objectifs:
        valeur = actuals.get(o.metrique)
        if valeur is None:
            continue
        cible = float(o.cible)
        atteint = valeur >= cible if o.sens == "min" else valeur <= cible
        meta = METRIQUES.get(o.metrique, {})
        lignes.append({
            "id": o.id,
            "metrique": o.metrique,
            "label": meta.get("label", o.metrique),
            "unite": meta.get("unite", ""),
            "sens": o.sens,
            "cible": cible,
            "valeur": valeur,
            "atteint": atteint,
            "ecart": round(valeur - cible, 2),
        })
    return lignes
