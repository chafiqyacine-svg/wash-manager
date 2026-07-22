"""Table `objectifs` — cibles de pilotage par site (CA, conformité…).

Le gérant fixe des seuils (ex. CA journalier ≥ 3000 DH, taux de conformité
≥ 90 %, lavages non facturés ≤ 2). Le système compare chaque jour la valeur
réelle à la cible et signale les écarts. `sens` = "min" (plancher à atteindre)
ou "max" (plafond à ne pas dépasser). `site_id` NULL = objectif global.
"""
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Objectif(Base):
    __tablename__ = "objectifs"

    id: Mapped[int] = mapped_column(primary_key=True)
    site_id: Mapped[int | None] = mapped_column(ForeignKey("sites.id"), index=True)
    metrique: Mapped[str] = mapped_column(String(32), index=True)  # ca_journalier, …
    cible: Mapped[float] = mapped_column(Numeric(10, 2))
    sens: Mapped[str] = mapped_column(String(3), default="min")     # "min" | "max"
    actif: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
