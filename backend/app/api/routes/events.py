"""Ingestion des événements du pipeline IA — l'entrée du système côté backend."""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_ingest_key
from app.api.routes.live import manager as live_manager
from app.core.database import get_db
from app.models import Camera, Employe
from app.schemas.event import EventAck, EventIn
from app.services.ingestion import traiter_evenement

router = APIRouter(prefix="/events", tags=["events"], dependencies=[Depends(require_ingest_key)])


class HeartbeatIn(BaseModel):
    """Signal de vie périodique d'une caméra du pipeline edge."""
    camera_id: str
    site_id: int | None = None
    role: str | None = None
    frames_traitees: int = 0
    events_envoyes: int = 0
    outbox_en_attente: int = 0


@router.post("", response_model=EventAck)
def ingest_event(event: EventIn, db: Session = Depends(get_db)) -> EventAck:
    """Reçoit un événement (entrée, zone, plaque, badge, sortie) et l'applique."""
    txn = traiter_evenement(db, event)
    # Diffuse un signal de mise à jour aux dashboards connectés (temps réel).
    live_manager.notifier({"type": "update", "source": "event"})
    return EventAck(ok=True, transaction_id=txn.id if txn else None)


@router.post("/heartbeat")
def heartbeat(hb: HeartbeatIn, db: Session = Depends(get_db)) -> dict:
    """Enregistre le signal de vie d'une caméra (upsert par camera_id)."""
    cam = db.scalar(select(Camera).where(Camera.camera_id == hb.camera_id))
    if cam is None:
        cam = Camera(camera_id=hb.camera_id)
        db.add(cam)
    cam.site_id = hb.site_id
    cam.role = hb.role
    cam.frames_traitees = hb.frames_traitees
    cam.events_envoyes = hb.events_envoyes
    cam.outbox_en_attente = hb.outbox_en_attente
    cam.derniere_vue = datetime.now(timezone.utc)
    db.commit()
    live_manager.notifier({"type": "update", "source": "camera"})
    return {"ok": True}


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
