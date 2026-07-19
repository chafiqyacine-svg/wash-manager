"""Gestion des employés et de leurs métriques de performance (cf. section 8)."""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models import Employe
from app.schemas.common import EmployeOut

router = APIRouter(prefix="/employes", tags=["employes"],
                   dependencies=[Depends(get_current_user)])


@router.get("", response_model=list[EmployeOut])
def lister_employes(db: Session = Depends(get_db)):
    return db.scalars(select(Employe)).all()


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
