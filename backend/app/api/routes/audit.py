"""Journal d'audit : consultation des actions sensibles (admin / manager)."""
from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_role, resolve_site
from app.core.database import get_db
from app.models import JournalAudit, Utilisateur

router = APIRouter(prefix="/audit", tags=["audit"])


class AuditOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    utilisateur_email: str | None
    role: str | None
    action: str
    cible: str | None
    cible_id: int | None
    site_id: int | None
    details: dict | None


@router.get("", response_model=list[AuditOut])
def journal(
    db: Session = Depends(get_db),
    user: Utilisateur = Depends(require_role("admin", "manager")),
    site_id: int | None = Depends(resolve_site),
    action: str | None = None,
    limit: int = 100,
):
    """Dernières actions journalisées. Un manager ne voit que son site."""
    stmt = select(JournalAudit).order_by(JournalAudit.created_at.desc())
    if site_id:
        stmt = stmt.where(JournalAudit.site_id == site_id)
    if action:
        stmt = stmt.where(JournalAudit.action == action)
    return db.scalars(stmt.limit(min(limit, 500))).all()
