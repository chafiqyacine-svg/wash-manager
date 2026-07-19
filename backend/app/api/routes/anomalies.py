"""Consultation et résolution des anomalies."""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models import Anomalie
from app.schemas.common import AnomalieOut

router = APIRouter(prefix="/anomalies", tags=["anomalies"],
                   dependencies=[Depends(get_current_user)])


@router.get("", response_model=list[AnomalieOut])
def lister_anomalies(db: Session = Depends(get_db), resolu: bool | None = None):
    stmt = select(Anomalie).order_by(Anomalie.heure.desc())
    if resolu is not None:
        stmt = stmt.where(Anomalie.resolu == resolu)
    return db.scalars(stmt).all()


@router.post("/{anomalie_id}/resoudre", response_model=AnomalieOut)
def resoudre_anomalie(anomalie_id: int, db: Session = Depends(get_db)):
    anomalie = db.get(Anomalie, anomalie_id)
    anomalie.resolu = True
    db.commit()
    return anomalie
