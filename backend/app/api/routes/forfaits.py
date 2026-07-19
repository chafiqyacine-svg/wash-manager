"""Configuration des forfaits (nom, prix, zones requises, seuils de temps)."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models import Forfait, Ticket, Transaction
from app.schemas.common import ForfaitCreate, ForfaitOut, ForfaitUpdate

router = APIRouter(prefix="/forfaits", tags=["forfaits"],
                   dependencies=[Depends(get_current_user)])


@router.get("", response_model=list[ForfaitOut])
def lister_forfaits(db: Session = Depends(get_db)):
    return db.scalars(select(Forfait)).all()


@router.post("", response_model=ForfaitOut, status_code=status.HTTP_201_CREATED)
def creer_forfait(payload: ForfaitCreate, db: Session = Depends(get_db)) -> Forfait:
    """Ajoute un nouveau service/forfait."""
    if db.scalar(select(Forfait).where(Forfait.nom == payload.nom)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Un forfait porte déjà ce nom")
    forfait = Forfait(**payload.model_dump())
    db.add(forfait)
    db.commit()
    db.refresh(forfait)
    return forfait


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


@router.delete("/{forfait_id}", status_code=status.HTTP_204_NO_CONTENT)
def supprimer_forfait(forfait_id: int, db: Session = Depends(get_db)) -> None:
    """Supprime un forfait — refusé s'il est déjà référencé (préserve l'historique)."""
    forfait = db.get(Forfait, forfait_id)
    if forfait is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Forfait inconnu")
    utilise = (
        db.scalar(select(Transaction.id).where(Transaction.forfait_id == forfait_id))
        or db.scalar(select(Ticket.id).where(Ticket.forfait_id == forfait_id))
    )
    if utilise:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Forfait utilisé par des transactions/tickets — suppression impossible.",
        )
    db.delete(forfait)
    db.commit()
