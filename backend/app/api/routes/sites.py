"""Sites (emplacements de lavage) — sélecteur multi-sites du dashboard."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models import Site, Utilisateur

router = APIRouter(prefix="/sites", tags=["sites"],
                   dependencies=[Depends(get_current_user)])


class SiteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nom: str
    adresse: str | None
    actif: bool


class SiteCreate(BaseModel):
    nom: str
    adresse: str | None = None


@router.get("", response_model=list[SiteOut])
def lister_sites(db: Session = Depends(get_db),
                 user: Utilisateur = Depends(get_current_user)):
    stmt = select(Site).where(Site.actif.is_(True))
    # Un manager/caissier rattaché à un site ne voit que le sien.
    if user.role != "admin" and user.site_id is not None:
        stmt = stmt.where(Site.id == user.site_id)
    return db.scalars(stmt).all()


@router.post("", response_model=SiteOut, status_code=201)
def creer_site(payload: SiteCreate, db: Session = Depends(get_db)) -> Site:
    site = Site(nom=payload.nom, adresse=payload.adresse)
    db.add(site)
    db.commit()
    db.refresh(site)
    return site
