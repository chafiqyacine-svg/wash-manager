"""Baies / stations de lavage — panneau « Wash Bay Stations » du dashboard.

Renvoie, par baie : état, effectif, lavage en cours (véhicule + catégorie +
temps écoulé), file d'attente et temps moyen du jour. Filtrable par site et par
statut (operational / out_of_service / all).
"""
from datetime import date, datetime, time, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, resolve_site
from app.api.routes.live import manager as live_manager
from app.core.database import get_db
from app.models import Bay, Forfait, Site, Transaction
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
    site_id: int | None = Depends(resolve_site),
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
            "site_nom": bay.site.nom if bay.site else None,
            "statut": bay.statut,
            "staff": bay.staff,
            "current_wash": current_wash,
            "in_queue": in_queue,
            "avg_time_min": avg_time,
        })
    return resultat


class BayCreate(BaseModel):
    site_id: int
    numero: int
    staff: int = 0


class BayUpdate(BaseModel):
    statut: str | None = None   # operationnelle | hors_service
    staff: int | None = None


@router.post("", status_code=status.HTTP_201_CREATED)
def creer_bay(payload: BayCreate, db: Session = Depends(get_db)) -> dict:
    if db.get(Site, payload.site_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Site inconnu")
    bay = Bay(site_id=payload.site_id, numero=payload.numero, staff=payload.staff,
              statut=BayStatut.OPERATIONNELLE.value)
    db.add(bay)
    db.commit()
    db.refresh(bay)
    live_manager.notifier({"type": "update", "source": "bay"})
    return {"id": bay.id, "numero": bay.numero, "site_id": bay.site_id}


@router.patch("/{bay_id}")
def modifier_bay(bay_id: int, payload: BayUpdate, db: Session = Depends(get_db)) -> dict:
    """Change l'état (opérationnelle / hors service) et/ou l'effectif d'une baie."""
    bay = db.get(Bay, bay_id)
    if bay is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Baie inconnue")
    if payload.statut is not None:
        if payload.statut not in {s.value for s in BayStatut}:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Statut invalide")
        bay.statut = payload.statut
    if payload.staff is not None:
        bay.staff = payload.staff
    db.commit()
    live_manager.notifier({"type": "update", "source": "bay"})
    return {"id": bay.id, "statut": bay.statut, "staff": bay.staff}
