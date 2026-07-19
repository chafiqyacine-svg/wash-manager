"""Sites (emplacements de lavage) — sélecteur multi-sites du dashboard."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models import Site

router = APIRouter(prefix="/sites", tags=["sites"],
                   dependencies=[Depends(get_current_user)])


class SiteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nom: str
    adresse: str | None
    actif: bool


@router.get("", response_model=list[SiteOut])
def lister_sites(db: Session = Depends(get_db)):
    return db.scalars(select(Site).where(Site.actif.is_(True))).all()
