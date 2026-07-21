"""Inventaire des consommables (stock par site + alertes de réapprovisionnement)."""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, resolve_site
from app.core.database import get_db
from app.models import Produit

router = APIRouter(prefix="/produits", tags=["inventaire"],
                   dependencies=[Depends(get_current_user)])


class ProduitOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    site_id: int | None
    nom: str
    unite: str
    quantite: float
    seuil_alerte: float
    prix_unitaire: float
    actif: bool


class ProduitCreate(BaseModel):
    nom: str
    site_id: int | None = None
    unite: str = "unité"
    quantite: float = 0
    seuil_alerte: float = 0
    prix_unitaire: float = 0


class ProduitUpdate(BaseModel):
    nom: str | None = None
    unite: str | None = None
    quantite: float | None = None
    seuil_alerte: float | None = None
    prix_unitaire: float | None = None
    actif: bool | None = None


@router.get("", response_model=list[ProduitOut])
def lister(db: Session = Depends(get_db), site_id: int | None = Depends(resolve_site),
           sous_seuil: bool = False):
    stmt = select(Produit).where(Produit.actif.is_(True)).order_by(Produit.nom)
    if site_id:
        stmt = stmt.where(Produit.site_id == site_id)
    produits = db.scalars(stmt).all()
    if sous_seuil:
        produits = [p for p in produits if float(p.quantite) <= float(p.seuil_alerte)]
    return produits


@router.post("", response_model=ProduitOut, status_code=status.HTTP_201_CREATED)
def creer(payload: ProduitCreate, db: Session = Depends(get_db)) -> Produit:
    produit = Produit(**payload.model_dump())
    db.add(produit)
    db.commit()
    db.refresh(produit)
    return produit


@router.patch("/{produit_id}", response_model=ProduitOut)
def modifier(produit_id: int, payload: ProduitUpdate, db: Session = Depends(get_db)) -> Produit:
    produit = db.get(Produit, produit_id)
    if produit is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Produit inconnu")
    for champ, valeur in payload.model_dump(exclude_none=True).items():
        setattr(produit, champ, valeur)
    db.commit()
    db.refresh(produit)
    return produit


@router.post("/{produit_id}/mouvement", response_model=ProduitOut)
def mouvement(produit_id: int, delta: float, db: Session = Depends(get_db)) -> Produit:
    """Entrée (+) ou sortie (-) de stock. La quantité ne descend pas sous 0."""
    produit = db.get(Produit, produit_id)
    if produit is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Produit inconnu")
    produit.quantite = max(0, float(produit.quantite) + delta)
    db.commit()
    db.refresh(produit)
    # TODO(dev): journaliser le mouvement (table mouvements_stock) + alerte si bas.
    return produit


@router.delete("/{produit_id}", status_code=status.HTTP_204_NO_CONTENT)
def supprimer(produit_id: int, db: Session = Depends(get_db)) -> None:
    produit = db.get(Produit, produit_id)
    if produit is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Produit inconnu")
    produit.actif = False  # suppression logique (préserve l'historique)
    db.commit()
