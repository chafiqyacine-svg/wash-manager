"""Consultation de l'historique des transactions (recherche/filtres)."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models import Transaction
from app.schemas.common import TransactionOut

router = APIRouter(prefix="/transactions", tags=["transactions"],
                   dependencies=[Depends(get_current_user)])


@router.get("", response_model=list[TransactionOut])
def lister_transactions(
    db: Session = Depends(get_db),
    limit: int = Query(50, le=200),
    offset: int = 0,
    # TODO(dev): ajouter filtres plaque, date, employe_id, conforme, anomalie
):
    stmt = select(Transaction).order_by(Transaction.id.desc()).limit(limit).offset(offset)
    return db.scalars(stmt).all()


@router.get("/{transaction_id}", response_model=TransactionOut)
def detail_transaction(transaction_id: int, db: Session = Depends(get_db)):
    return db.get(Transaction, transaction_id)
