"""Configuration des forfaits (nom, prix, zones requises, seuils de temps)."""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models import Forfait
from app.schemas.common import ForfaitOut

router = APIRouter(prefix="/forfaits", tags=["forfaits"],
                   dependencies=[Depends(get_current_user)])


@router.get("", response_model=list[ForfaitOut])
def lister_forfaits(db: Session = Depends(get_db)):
    return db.scalars(select(Forfait)).all()


# TODO(dev): endpoints PUT/PATCH pour ajuster prix, zones_requises et seuils
#   depuis l'écran Configuration du dashboard.
