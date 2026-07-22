"""Alertes : historique des notifications + envoi d'un test (admin/manager)."""
from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_role, resolve_site
from app.core.database import get_db
from app.models import Notification, Utilisateur
from app.schemas.common import ORMModel
from app.services.notifications import _canaux_configures, notifier

router = APIRouter(prefix="/notifications", tags=["notifications"])


class NotificationOut(ORMModel):
    id: int
    cree_at: datetime
    canal: str
    destinataire: str | None
    sujet: str
    message: str
    severite: str | None
    statut: str
    site_id: int | None
    ref_type: str | None
    ref_id: int | None


@router.get("", response_model=list[NotificationOut])
def historique(db: Session = Depends(get_db),
               user: Utilisateur = Depends(require_role("admin", "manager")),
               site_id: int | None = Depends(resolve_site), limit: int = 100):
    stmt = select(Notification).order_by(Notification.cree_at.desc())
    if site_id:
        stmt = stmt.where(Notification.site_id == site_id)
    return db.scalars(stmt.limit(min(limit, 500))).all()


@router.get("/canaux")
def canaux(user: Utilisateur = Depends(require_role("admin", "manager"))) -> dict:
    """Canaux d'alerte réellement configurés (sinon : mode simulé)."""
    actifs = _canaux_configures()
    return {"canaux": actifs, "mode": "reel" if actifs else "simule"}


@router.post("/test", response_model=list[NotificationOut])
def envoyer_test(db: Session = Depends(get_db),
                 user: Utilisateur = Depends(require_role("admin", "manager"))):
    """Envoie une alerte de test (vérifie le paramétrage des canaux)."""
    return notifier(db, "Test d'alerte Wash Manager",
                    f"Notification de test déclenchée par {user.email}.",
                    severite="basse", site_id=user.site_id)
