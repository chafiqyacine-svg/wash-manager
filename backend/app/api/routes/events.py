"""Ingestion des événements du pipeline IA — l'entrée du système côté backend."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_ingest_key
from app.api.routes.live import manager as live_manager
from app.core.database import get_db
from app.schemas.event import EventAck, EventIn
from app.services.ingestion import traiter_evenement

router = APIRouter(prefix="/events", tags=["events"], dependencies=[Depends(require_ingest_key)])


@router.post("", response_model=EventAck)
def ingest_event(event: EventIn, db: Session = Depends(get_db)) -> EventAck:
    """Reçoit un événement (entrée, zone, plaque, badge, sortie) et l'applique."""
    txn = traiter_evenement(db, event)
    # Diffuse un signal de mise à jour aux dashboards connectés (temps réel).
    live_manager.notifier({"type": "update", "source": "event"})
    return EventAck(ok=True, transaction_id=txn.id if txn else None)
