"""Table `journal_audit` — traçabilité des actions sensibles (contrôle interne).

Chaque action à risque (annulation de ticket, changement de prix, résolution
d'anomalie, clôture de caisse, ajustement de stock…) y est journalisée avec
QUI l'a faite, QUAND, sur QUOI. C'est l'outil de contrôle du gérant : on ne
voit plus seulement les résultats, mais aussi les interventions humaines.

L'email/rôle de l'utilisateur est copié (snapshot) pour rester lisible même si
le compte est ensuite modifié ou supprimé.
"""
from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class JournalAudit(Base):
    __tablename__ = "journal_audit"

    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    utilisateur_id: Mapped[int | None] = mapped_column(ForeignKey("utilisateurs.id"))
    utilisateur_email: Mapped[str | None] = mapped_column(String(255))  # snapshot
    role: Mapped[str | None] = mapped_column(String(16))

    action: Mapped[str] = mapped_column(String(64), index=True)  # ex: "ticket.annuler"
    cible: Mapped[str | None] = mapped_column(String(32))         # ex: "ticket"
    cible_id: Mapped[int | None] = mapped_column(Integer)
    site_id: Mapped[int | None] = mapped_column(ForeignKey("sites.id"), index=True)
    details: Mapped[dict | None] = mapped_column(JSON)
