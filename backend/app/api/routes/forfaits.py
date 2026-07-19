"""Configuration des forfaits (nom, prix, zones requises, seuils de temps)."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models import Forfait
from app.schemas.common import ForfaitOut, ForfaitUpdate

router = APIRouter(prefix="/forfaits", tags=["forfaits"],
                   dependencies=[Depends(get_current_user)])


@router.get("", response_model=list[ForfaitOut])
def lister_forfaits(db: Session = Depends(get_db)):
    return db.scalars(select(Forfait)).all()


@router.put("/{forfait_id}", response_model=ForfaitOut)
def modifier_forfait(
    forfait_id: int, payload: ForfaitUpdate, db: Session = Depends(get_db)
) -> Forfait:
    """Ajuste prix, zones requises et seuils de temps d'un forfait."""
    forfait = db.get(Forfait, forfait_id)
    if forfait is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Forfait inconnu")
    data = payload.model_dump(exclude_none=True)
    for champ, valeur in data.items():
        setattr(forfait, champ, valeur)
    db.commit()
    db.refresh(forfait)
    return forfait
