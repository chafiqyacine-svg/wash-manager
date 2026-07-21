"""Marge par forfait — coût des consommables et rentabilité, par site."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, resolve_site
from app.core.database import get_db
from app.models import Forfait
from app.services.marge import marge_forfait, marges

router = APIRouter(prefix="/marges", tags=["marges"],
                   dependencies=[Depends(get_current_user)])


@router.get("")
def lister_marges(db: Session = Depends(get_db),
                  site_id: int | None = Depends(resolve_site)):
    """Marge de chaque forfait. `site_id` restreint aux produits d'un site."""
    return marges(db, site_id)


@router.get("/{forfait_id}")
def marge_du_forfait(forfait_id: int, db: Session = Depends(get_db),
                     site_id: int | None = Depends(resolve_site)):
    forfait = db.get(Forfait, forfait_id)
    if forfait is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Forfait inconnu")
    return marge_forfait(db, forfait, site_id)
