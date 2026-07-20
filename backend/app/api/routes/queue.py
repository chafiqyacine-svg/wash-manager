"""Queue Management — file d'attente et mode d'exploitation MANUEL.

Utile tant que les caméras ne sont pas installées : la station fonctionne à la
main. Flux :
  1. La caisse crée un ticket (forfait payé)      -> il entre dans la file (« In order »).
  2. L'opérateur DÉMARRE le lavage sur une baie    -> transaction « en_cours ».
  3. L'opérateur TERMINE le lavage                 -> transaction « cloturee », conforme.

En mode caméra (IA), les transactions sont créées automatiquement par les
événements ; ce mode manuel est un complément, pas un remplacement.
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, resolve_site
from app.api.routes.live import manager as live_manager
from app.core.database import get_db
from app.models import Bay, Ticket, Transaction, Vehicule

router = APIRouter(prefix="/queue", tags=["queue"],
                   dependencies=[Depends(get_current_user)])


@router.get("")
def file_attente(db: Session = Depends(get_db), site_id: int | None = Depends(resolve_site)) -> dict:
    """File d'attente (tickets payés non démarrés) + lavages en cours."""
    en_attente = db.scalars(
        select(Ticket).where(Ticket.statut == "ouvert",
                             Ticket.transaction_id.is_(None))
        .order_by(Ticket.heure)
    ).all()

    stmt = select(Transaction).where(Transaction.statut == "en_cours")
    if site_id:
        bay_ids = list(db.scalars(select(Bay.id).where(Bay.site_id == site_id)).all())
        stmt = stmt.where(Transaction.bay_id.in_(bay_ids))
    en_cours = db.scalars(stmt.order_by(Transaction.heure_entree)).all()

    return {
        "en_attente": [
            {"ticket_id": t.id, "forfait_id": t.forfait_id, "prix": float(t.prix),
             "plaque": t.plaque, "heure": t.heure}
            for t in en_attente
        ],
        "en_cours": [
            {"transaction_id": tx.id, "bay_id": tx.bay_id,
             "plaque": tx.vehicule.plaque if tx.vehicule else tx.track_id,
             "heure_entree": tx.heure_entree}
            for tx in en_cours
        ],
    }


@router.post("/demarrer")
def demarrer(ticket_id: int, bay_id: int, db: Session = Depends(get_db)) -> dict:
    """Assigne un ticket à une baie et démarre le lavage (transaction en_cours)."""
    ticket = db.get(Ticket, ticket_id)
    if ticket is None or ticket.statut != "ouvert" or ticket.transaction_id is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Ticket indisponible")
    bay = db.get(Bay, bay_id)
    if bay is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Baie inconnue")

    vehicule = None
    if ticket.plaque:
        vehicule = db.scalar(select(Vehicule).where(Vehicule.plaque == ticket.plaque))
        if vehicule is None:
            vehicule = Vehicule(plaque=ticket.plaque, nombre_visites=0)
            db.add(vehicule)
            db.flush()

    txn = Transaction(
        vehicule_id=vehicule.id if vehicule else None,
        forfait_id=ticket.forfait_id,
        bay_id=bay_id,
        heure_entree=datetime.now(timezone.utc),
        statut="en_cours",
    )
    db.add(txn)
    db.flush()
    ticket.transaction_id = txn.id  # lien pour la clôture
    db.commit()
    live_manager.notifier({"type": "update", "source": "queue"})
    return {"transaction_id": txn.id, "bay_id": bay_id}


@router.post("/terminer")
def terminer(transaction_id: int, db: Session = Depends(get_db)) -> dict:
    """Clôture un lavage manuel : conforme au forfait payé (opérateur de confiance)."""
    txn = db.get(Transaction, transaction_id)
    if txn is None or txn.statut != "en_cours":
        raise HTTPException(status.HTTP_409_CONFLICT, "Transaction non en cours")

    txn.heure_sortie = datetime.now(timezone.utc)
    if txn.heure_entree:
        debut = txn.heure_entree
        if debut.tzinfo is None:
            debut = debut.replace(tzinfo=timezone.utc)
        txn.duree_totale = int((txn.heure_sortie - debut).total_seconds())
    txn.statut = "cloturee"

    # Mode manuel : le forfait payé fait foi (pas de détection par zones).
    ticket = db.scalar(select(Ticket).where(Ticket.transaction_id == txn.id))
    if ticket is not None:
        txn.forfait_detecte = ticket.forfait.nom
        txn.conforme = True
        ticket.statut = "rapproche"
    db.commit()
    live_manager.notifier({"type": "update", "source": "queue"})
    return {"transaction_id": txn.id, "statut": txn.statut}
