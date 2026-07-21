"""Caisse intégrée : création et consultation des tickets.

Écran « Caisse » du dashboard : l'opérateur crée un ticket à l'encaissement.
Ce ticket sera rapproché automatiquement de la transaction détectée par l'IA.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.routes.live import manager as live_manager
from app.core.database import get_db
from app.models import Forfait, Ticket, Transaction, Utilisateur
from app.schemas.ticket import TicketCreate, TicketOut
from app.services.ingestion import finaliser_transaction

router = APIRouter(prefix="/tickets", tags=["caisse"],
                   dependencies=[Depends(get_current_user)])


@router.post("", response_model=TicketOut, status_code=status.HTTP_201_CREATED)
def creer_ticket(payload: TicketCreate, db: Session = Depends(get_db),
                 user: Utilisateur = Depends(get_current_user)) -> Ticket:
    forfait = db.get(Forfait, payload.forfait_id)
    if forfait is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Forfait inconnu")
    # Site d'encaissement : celui du caissier rattaché, sinon celui saisi.
    site_id = user.site_id if (user.role != "admin" and user.site_id) else payload.site_id
    ticket = Ticket(
        forfait_id=forfait.id,
        prix=forfait.prix,
        plaque=payload.plaque,
        employe_id=payload.employe_id,
        reference=payload.reference,
        mode_paiement=payload.mode_paiement or "espece",
        site_id=site_id,
        statut="ouvert",
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    live_manager.notifier({"type": "update", "source": "ticket"})
    return ticket


@router.get("", response_model=list[TicketOut])
def lister_tickets(db: Session = Depends(get_db), statut: str | None = None):
    stmt = select(Ticket).order_by(Ticket.heure.desc())
    if statut:
        stmt = stmt.where(Ticket.statut == statut)
    return db.scalars(stmt).all()


@router.post("/{ticket_id}/annuler", response_model=TicketOut)
def annuler_ticket(ticket_id: int, db: Session = Depends(get_db)) -> Ticket:
    ticket = db.get(Ticket, ticket_id)
    if ticket is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Ticket inconnu")
    ticket.statut = "annule"
    db.commit()
    db.refresh(ticket)
    live_manager.notifier({"type": "update", "source": "ticket"})
    return ticket


@router.post("/{ticket_id}/rapprocher", response_model=TicketOut)
def rapprocher_manuellement(
    ticket_id: int, transaction_id: int, db: Session = Depends(get_db)
) -> Ticket:
    """Associe manuellement un ticket ouvert à une transaction et recalcule
    conformité + anomalies (utile pour les cas ambigus non appariés auto).
    """
    ticket = db.get(Ticket, ticket_id)
    if ticket is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Ticket inconnu")
    if ticket.statut != "ouvert":
        raise HTTPException(status.HTTP_409_CONFLICT, "Ticket déjà traité")
    txn = db.get(Transaction, transaction_id)
    if txn is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Transaction inconnue")

    finaliser_transaction(db, txn, ticket)
    db.commit()
    db.refresh(ticket)
    live_manager.notifier({"type": "update", "source": "ticket"})
    return ticket
