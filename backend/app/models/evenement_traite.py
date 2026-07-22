"""Table `evenements_traites` — idempotence de l'ingestion.

La file locale de l'edge (outbox) peut RE-livrer un événement si l'accusé de
réception a été perdu (coupure réseau juste après le POST). Pour éviter de
l'appliquer deux fois (double transaction, double visite véhicule…), on mémorise
l'`event_id` unique de chaque événement déjà traité et on ignore les doublons.

TODO(dev): purger périodiquement les lignes anciennes (> quelques jours) — la
fenêtre de re-livraison de l'edge est courte, inutile de tout conserver.
"""
from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class EvenementTraite(Base):
    __tablename__ = "evenements_traites"

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    type: Mapped[str | None] = mapped_column(String(32))
    track_id: Mapped[str | None] = mapped_column(String(64))
    cree_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
