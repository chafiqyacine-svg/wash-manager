"""Consultation des véhicules et correction manuelle des plaques."""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models import Vehicule
from app.schemas.common import VehiculeOut

router = APIRouter(prefix="/vehicules", tags=["vehicules"],
                   dependencies=[Depends(get_current_user)])


@router.get("", response_model=list[VehiculeOut])
def lister_vehicules(db: Session = Depends(get_db), plaque: str | None = None):
    stmt = select(Vehicule)
    if plaque:
        stmt = stmt.where(Vehicule.plaque.ilike(f"%{plaque}%"))
    return db.scalars(stmt).all()


# TODO(dev): endpoint de correction manuelle de plaque (LPR échoué) — associe
#   la plaque saisie à la transaction et lève/résout l'anomalie PLAQUE_NON_LUE.
