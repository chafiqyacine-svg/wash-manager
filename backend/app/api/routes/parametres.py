"""Paramètres configurables (écran Configuration)."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.services import parametres as svc

router = APIRouter(prefix="/parametres", tags=["configuration"],
                   dependencies=[Depends(get_current_user)])


class ParametreUpdate(BaseModel):
    valeur: str


@router.get("")
def lister(db: Session = Depends(get_db)) -> dict[str, str]:
    return svc.lister_params(db)


@router.put("/{cle}")
def modifier(cle: str, payload: ParametreUpdate, db: Session = Depends(get_db)) -> dict:
    p = svc.set_param(db, cle, payload.valeur)
    return {"cle": p.cle, "valeur": p.valeur}
