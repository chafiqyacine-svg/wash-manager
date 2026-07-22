"""Ingestion des événements du pipeline IA — l'entrée du système côté backend."""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_ingest_key
from app.api.routes.live import manager as live_manager
from app.core.database import get_db
from app.models import Employe
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


@router.get("/palette-gilets")
def palette_gilets(db: Session = Depends(get_db), site_id: int | None = None) -> dict:
    """Couleurs de gilet enregistrées (employés actifs) — pour le pipeline edge.

    Le edge charge cette palette au démarrage pour ramener la couleur mesurée
    à une valeur canonique (rapprochement backend exact). Protégé par la clé
    d'ingestion (endpoint edge, pas de JWT).
    """
    stmt = select(Employe.couleur_gilet).where(
        Employe.actif.is_(True), Employe.couleur_gilet.is_not(None)
    )
    if site_id:
        stmt = stmt.where(Employe.site_id == site_id)
    couleurs = sorted({c for c in db.scalars(stmt).all() if c})
    return {"couleurs": couleurs}
