"""Configuration des forfaits (nom, prix, zones requises, seuils de temps)."""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models import Forfait, ForfaitProduit, Ticket, Transaction, Utilisateur
from app.schemas.common import ForfaitCreate, ForfaitOut, ForfaitUpdate
from app.services.audit import journaliser

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
    forfait_id: int, payload: ForfaitUpdate, db: Session = Depends(get_db),
    user: Utilisateur = Depends(get_current_user),
) -> Forfait:
    """Ajuste prix, zones requises et seuils de temps d'un forfait."""
    forfait = db.get(Forfait, forfait_id)
    if forfait is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Forfait inconnu")
    data = payload.model_dump(exclude_none=True)
    ancien_prix = float(forfait.prix)
    for champ, valeur in data.items():
        setattr(forfait, champ, valeur)
    db.commit()
    db.refresh(forfait)
    journaliser(db, user, "forfait.modifier", cible="forfait", cible_id=forfait.id,
                details={"champs": list(data.keys()), "ancien_prix": ancien_prix,
                         "nouveau_prix": float(forfait.prix)})
    return forfait


# ─── Recette de consommation (forfait → produits) ────────────────────────────
class ConsommationItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    produit_id: int
    lavages_par_unite: int


@router.get("/{forfait_id}/consommation", response_model=list[ConsommationItem])
def consommation(forfait_id: int, db: Session = Depends(get_db)):
    return db.scalars(
        select(ForfaitProduit).where(ForfaitProduit.forfait_id == forfait_id)
    ).all()


@router.put("/{forfait_id}/consommation", response_model=list[ConsommationItem])
def maj_consommation(forfait_id: int, items: list[ConsommationItem],
                     db: Session = Depends(get_db)):
    """Définit la recette : quels produits ce forfait consomme et à quel rythme."""
    if db.get(Forfait, forfait_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Forfait inconnu")
    db.execute(delete(ForfaitProduit).where(ForfaitProduit.forfait_id == forfait_id))
    for it in items:
        db.add(ForfaitProduit(forfait_id=forfait_id, produit_id=it.produit_id,
                              lavages_par_unite=max(1, it.lavages_par_unite)))
    db.commit()
    return consommation(forfait_id, db)


@router.delete("/{forfait_id}", status_code=status.HTTP_204_NO_CONTENT)
def supprimer_forfait(forfait_id: int, db: Session = Depends(get_db),
                      user: Utilisateur = Depends(get_current_user)) -> None:
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
    nom = forfait.nom
    db.delete(forfait)
    db.commit()
    journaliser(db, user, "forfait.supprimer", cible="forfait", cible_id=forfait_id,
                details={"nom": nom})
