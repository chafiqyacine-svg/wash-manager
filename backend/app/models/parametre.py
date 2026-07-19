"""Table `parametres` — configuration modifiable depuis le dashboard.

Stockage clé-valeur simple (extensible) pour les seuils réglables : fenêtre de
rapprochement, heure du rapport, etc. Lu via services/parametres.py.
"""
from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Parametre(Base):
    __tablename__ = "parametres"

    cle: Mapped[str] = mapped_column(String(64), primary_key=True)
    valeur: Mapped[str] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
