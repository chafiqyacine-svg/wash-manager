"""Journalisation des actions sensibles (contrôle interne).

`journaliser` est appelé par les routes après une action à risque. On copie
l'email/rôle de l'utilisateur (snapshot) pour une trace lisible et durable.
"""
from typing import Any

from sqlalchemy.orm import Session

from app.models import JournalAudit, Utilisateur


def journaliser(
    db: Session,
    user: Utilisateur | None,
    action: str,
    *,
    cible: str | None = None,
    cible_id: int | None = None,
    details: dict[str, Any] | None = None,
    site_id: int | None = None,
    commit: bool = True,
) -> JournalAudit:
    """Enregistre une entrée d'audit. `action` en notation « cible.verbe »."""
    entry = JournalAudit(
        utilisateur_id=getattr(user, "id", None),
        utilisateur_email=getattr(user, "email", None),
        role=getattr(user, "role", None),
        action=action,
        cible=cible,
        cible_id=cible_id,
        details=details,
        site_id=site_id if site_id is not None else getattr(user, "site_id", None),
    )
    db.add(entry)
    if commit:
        db.commit()
    return entry
