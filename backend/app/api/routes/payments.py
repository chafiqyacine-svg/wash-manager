"""Paiements — vue financière (panneau « Transactions » + page Payments).

Statut de paiement dérivé de l'état de la transaction :
  - Paid    : la transaction est rapprochée d'un ticket (forfait_id renseigné).
  - Pending : véhicule lavé mais sans ticket (montant estimé d'après le forfait
              détecté) — c'est une recette en attente / lavage non facturé.
"""
from datetime import date, datetime, time, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models import Bay, Forfait, Transaction

router = APIRouter(prefix="/payments", tags=["payments"],
                   dependencies=[Depends(get_current_user)])


@router.get("")
def lister_paiements(
    db: Session = Depends(get_db),
    site_id: int | None = None,
    limit: int = 30,
) -> dict:
    prix_par_id = {f.id: float(f.prix) for f in db.scalars(select(Forfait)).all()}
    prix_par_nom = {f.nom: float(f.prix) for f in db.scalars(select(Forfait)).all()}

    stmt = (
        select(Transaction)
        .where(Transaction.statut == "cloturee")
        .order_by(Transaction.heure_sortie.desc())
        .limit(limit)
    )
    if site_id:
        bay_ids = list(db.scalars(select(Bay.id).where(Bay.site_id == site_id)).all())
        stmt = stmt.where(Transaction.bay_id.in_(bay_ids))
    txns = db.scalars(stmt).all()

    items = []
    total_paid = 0.0
    total_pending = 0.0
    for t in txns:
        if t.forfait_id:
            statut = "paid"
            montant = prix_par_id.get(t.forfait_id, 0.0)
            total_paid += montant
        else:
            statut = "pending"
            montant = prix_par_nom.get(t.forfait_detecte, 0.0)
            total_pending += montant
        items.append({
            "transaction_id": t.id,
            "vehicule": t.vehicule.plaque if t.vehicule else t.track_id,
            "montant": round(montant, 2),
            "statut": statut,
            "heure": t.heure_sortie,
        })

    return {
        "items": items,
        "total_paid": round(total_paid, 2),
        "total_pending": round(total_pending, 2),
    }
