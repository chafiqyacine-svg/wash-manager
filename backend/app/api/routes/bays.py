"""Baies / stations de lavage — panneau « Wash Bay Stations » du dashboard.

Renvoie, par baie : état, effectif, lavage en cours (véhicule + catégorie +
temps écoulé), file d'attente et temps moyen du jour. Filtrable par site et par
statut (operational / out_of_service / all).
"""
from datetime import date, datetime, time, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models import Bay, Forfait, Transaction
from app.models.enums import BayStatut

router = APIRouter(prefix="/bays", tags=["bays"],
                   dependencies=[Depends(get_current_user)])


def _aware(dt: datetime | None) -> datetime | None:
    """Normalise en UTC-aware (SQLite renvoie des datetimes naïfs)."""
    if dt is not None and dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


@router.get("")
def lister_bays(
    db: Session = Depends(get_db),
    site_id: int | None = None,
    statut: str = Query("all", pattern="^(operational|out_of_service|all)$"),
) -> list[dict]:
    stmt = select(Bay).where(Bay.actif.is_(True)).order_by(Bay.numero)
    if site_id:
        stmt = stmt.where(Bay.site_id == site_id)
    if statut == "operational":
        stmt = stmt.where(Bay.statut == BayStatut.OPERATIONNELLE.value)
    elif statut == "out_of_service":
        stmt = stmt.where(Bay.statut == BayStatut.HORS_SERVICE.value)
    bays = db.scalars(stmt).all()

    forfaits = {f.id: f.nom for f in db.scalars(select(Forfait)).all()}
    debut_jour = datetime.combine(date.today(), time.min)
    fin_jour = debut_jour + timedelta(days=1)
    maintenant = datetime.now(timezone.utc)

    resultat = []
    for bay in bays:
        # Lavage en cours sur cette baie (le plus récent).
        courant = db.scalar(
            select(Transaction).where(
                Transaction.bay_id == bay.id,
                Transaction.statut == "en_cours",
            ).order_by(Transaction.heure_entree.desc())
        )
        current_wash = None
        if courant is not None:
            elapsed = None
            if courant.heure_entree:
                elapsed = int((maintenant - _aware(courant.heure_entree)).total_seconds() / 60)
            current_wash = {
                "vehicule": courant.vehicule.plaque if courant.vehicule else courant.track_id,
                "categorie": forfaits.get(courant.forfait_id),
                "elapsed_min": elapsed,
            }

        # File d'attente = autres véhicules en cours sur la baie (hors le courant).
        # TODO(dev): modéliser une vraie file d'attente (ordre, heure d'arrivée).
        in_queue = db.query(Transaction).filter(
            Transaction.bay_id == bay.id, Transaction.statut == "en_cours"
        ).count()
        in_queue = max(0, in_queue - (1 if courant else 0))

        # Temps moyen du jour sur cette baie.
        durees = db.scalars(
            select(Transaction.duree_totale).where(
                Transaction.bay_id == bay.id,
                Transaction.statut == "cloturee",
                Transaction.heure_sortie >= debut_jour,
                Transaction.heure_sortie < fin_jour,
                Transaction.duree_totale.is_not(None),
            )
        ).all()
        avg_time = round(sum(durees) / len(durees) / 60) if durees else None

        resultat.append({
            "id": bay.id,
            "numero": bay.numero,
            "site_id": bay.site_id,
            "statut": bay.statut,
            "staff": bay.staff,
            "current_wash": current_wash,
            "in_queue": in_queue,
            "avg_time_min": avg_time,
        })
    return resultat
