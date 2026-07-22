"""Supervision des caméras : état EN LIGNE / HORS LIGNE pour le dashboard."""
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, resolve_site
from app.core.database import get_db
from app.models import Camera

router = APIRouter(prefix="/cameras", tags=["cameras"],
                   dependencies=[Depends(get_current_user)])

# Au-delà de ce délai sans heartbeat, une caméra est considérée HORS LIGNE.
SEUIL_HORS_LIGNE_S = 90


def _aware(dt: datetime | None) -> datetime | None:
    """Normalise en UTC aware (SQLite renvoie des datetimes naïfs)."""
    if dt is None:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


@router.get("")
def lister_cameras(db: Session = Depends(get_db),
                   site_id: int | None = Depends(resolve_site),
                   seuil_s: int = SEUIL_HORS_LIGNE_S) -> list[dict]:
    """Caméras connues + statut en ligne (heartbeat récent) / hors ligne."""
    stmt = select(Camera).order_by(Camera.camera_id)
    if site_id:
        stmt = stmt.where(Camera.site_id == site_id)
    maintenant = datetime.now(timezone.utc)
    limite = maintenant - timedelta(seconds=seuil_s)

    cameras = []
    for c in db.scalars(stmt).all():
        vue = _aware(c.derniere_vue)
        en_ligne = vue is not None and vue >= limite
        cameras.append({
            "camera_id": c.camera_id,
            "site_id": c.site_id,
            "role": c.role,
            "en_ligne": en_ligne,
            "derniere_vue": c.derniere_vue,
            "silence_s": int((maintenant - vue).total_seconds()) if vue else None,
            "frames_traitees": c.frames_traitees,
            "events_envoyes": c.events_envoyes,
            "outbox_en_attente": c.outbox_en_attente,
        })
    return cameras
