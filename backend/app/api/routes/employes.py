"""Gestion des employés et de leurs métriques de performance (cf. section 8)."""
from datetime import date, datetime, time, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models import Bay, Employe, Forfait, Transaction
from app.schemas.common import EmployeOut
from app.services.rapport import _perf_employes

router = APIRouter(prefix="/employes", tags=["employes"],
                   dependencies=[Depends(get_current_user)])


@router.get("", response_model=list[EmployeOut])
def lister_employes(db: Session = Depends(get_db)):
    return db.scalars(select(Employe)).all()


@router.get("/performance")
def performance(
    db: Session = Depends(get_db),
    jours: int = 7,
    site_id: int | None = None,
) -> list[dict]:
    """Classement des employés sur une période (véhicules, temps moyen, taux de
    conformité, revenus, score qualité), trié par score décroissant."""
    debut = datetime.combine(date.today() - timedelta(days=jours - 1), time.min)

    stmt = select(Transaction).where(
        Transaction.statut == "cloturee",
        Transaction.heure_sortie >= debut,
        Transaction.employe_id.is_not(None),
    )
    if site_id:
        bay_ids = list(db.scalars(select(Bay.id).where(Bay.site_id == site_id)).all())
        stmt = stmt.where(Transaction.bay_id.in_(bay_ids))
    txns = db.scalars(stmt).all()

    prix = {f.id: float(f.prix) for f in db.scalars(select(Forfait)).all()}
    noms = {e.id: e.nom for e in db.scalars(select(Employe)).all()}
    return _perf_employes(txns, prix, noms)


@router.get("/{employe_id}/metriques")
def metriques_employe(employe_id: int, db: Session = Depends(get_db)) -> dict:
    """Métriques d'un employé : véhicules/jour, temps moyen, taux conformité,
    temps mort, revenus générés, score qualité (cf. tableau 8.2).

    TODO(dev): calculer sur une période donnée (query params debut/fin).
    """
    return {
        "employe_id": employe_id,
        "vehicules_jour": 0,
        "temps_moyen_min": 0.0,
        "taux_conformite": 0.0,
        "temps_mort_min": 0.0,
        "revenus_generes": 0.0,
        "score_qualite": 0.0,
    }
