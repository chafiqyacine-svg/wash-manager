"""Rapports journaliers : consultation et génération à la demande."""
from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models import RapportJournalier
from app.services.rapport import generer_rapport_journalier

router = APIRouter(prefix="/rapports", tags=["rapports"],
                   dependencies=[Depends(get_current_user)])


@router.get("")
def lister_rapports(db: Session = Depends(get_db)):
    return db.scalars(
        select(RapportJournalier).order_by(RapportJournalier.date.desc())
    ).all()


@router.post("/generer")
def generer(jour: date, db: Session = Depends(get_db)):
    """Génère (ou régénère) le rapport d'un jour donné."""
    return generer_rapport_journalier(db, jour)
