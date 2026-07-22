"""Objectifs de pilotage : configuration des cibles + évaluation des écarts."""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_role, resolve_site
from app.core.database import get_db
from app.models import Objectif, Utilisateur
from app.services.objectifs import METRIQUES, evaluer

router = APIRouter(prefix="/objectifs", tags=["objectifs"],
                   dependencies=[Depends(get_current_user)])


class ObjectifIn(BaseModel):
    metrique: str
    cible: float
    sens: str | None = None            # défaut = sens de la métrique
    site_id: int | None = None


class ObjectifOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    site_id: int | None
    metrique: str
    cible: float
    sens: str
    actif: bool


@router.get("/metriques")
def metriques() -> list[dict]:
    """Métriques disponibles pour définir un objectif."""
    return [{"metrique": k, **v} for k, v in METRIQUES.items()]


@router.get("", response_model=list[ObjectifOut])
def lister(db: Session = Depends(get_db), site_id: int | None = Depends(resolve_site)):
    stmt = select(Objectif).where(Objectif.actif.is_(True)).order_by(Objectif.metrique)
    if site_id:
        stmt = stmt.where(Objectif.site_id == site_id)
    return db.scalars(stmt).all()


@router.get("/evaluation")
def evaluation(jour: date | None = None, db: Session = Depends(get_db),
               site_id: int | None = Depends(resolve_site)) -> list[dict]:
    """Écarts du jour : valeur réelle vs cible pour chaque objectif."""
    return evaluer(db, jour or date.today(), site_id)


@router.post("", response_model=ObjectifOut, status_code=status.HTTP_201_CREATED)
def creer(payload: ObjectifIn, db: Session = Depends(get_db),
          user: Utilisateur = Depends(require_role("admin", "manager"))) -> Objectif:
    if payload.metrique not in METRIQUES:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Métrique inconnue")
    # Sécurité multi-site : un manager rattaché fixe des objectifs pour son site.
    site_id = user.site_id if (user.role != "admin" and user.site_id) else payload.site_id
    sens = payload.sens or METRIQUES[payload.metrique]["sens"]
    # Un seul objectif actif par (site, métrique) : on remplace l'existant.
    existant = db.scalar(select(Objectif).where(
        Objectif.site_id == site_id, Objectif.metrique == payload.metrique,
        Objectif.actif.is_(True)))
    if existant:
        existant.cible = payload.cible
        existant.sens = sens
        db.commit()
        db.refresh(existant)
        return existant
    obj = Objectif(site_id=site_id, metrique=payload.metrique, cible=payload.cible, sens=sens)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/{objectif_id}", status_code=status.HTTP_204_NO_CONTENT)
def supprimer(objectif_id: int, db: Session = Depends(get_db),
              user: Utilisateur = Depends(require_role("admin", "manager"))) -> None:
    obj = db.get(Objectif, objectif_id)
    if obj is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Objectif inconnu")
    obj.actif = False
    db.commit()
